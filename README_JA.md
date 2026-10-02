# ChatGPT Conversation Recovery Dynamics — 日本語概要

これは、ChatGPTで「既存会話が開けない / 429になる / recoveryが完了しない」現象を、匿名化したHAR由来のイベント列から調べる独立ケーススタディです。

**OpenAI内部の根本原因を断定するものではありません。**

## まず結論

再検算したところ、Blocked時に観測周期が短くなる現象は、

「Blockedだからクライアントが意図的にretryを強くする」

と仮定しなくても説明できました。

公開データ106遷移では、

~~~text
次の観測までの時間
 ~= 5.616秒 + 0.957 × 現在のrequest処理時間

R^2 = 0.991
~~~

となっています。

つまり、

~~~text
request開始
 -> 成功/失敗が返る
 -> 約5.6秒待つ
 -> 次の観測
~~~

というcompletion-coupledな周期なら、

- Accessibleでは応答に約5秒かかる -> 周期は約10秒
- Blockedでは約0.3秒でfast-failする -> 周期は約6秒

となり、同じ待機ルールでもBlocked側の試行頻度が自然に上がります。

## このcaptureで再現できたこと

大きい方のHARだけを重複排除して解析しています。

- recovery関連イベント: 253
- stream status + conversation snapshot の観測ペア: 108
- Accessible: 48
- Blocked: 60
- 混合ペア: 0
- pair開始時刻の最大ずれ: 9ms

Blockedでは、

- snapshot: HTTP 429
- stream status: HTTP responseなし

が同時に観測されました。

観測間隔中央値:

- Accessible: 10.272秒
- Blocked: 5.998秒

snapshot latency中央値:

- Accessible: 約5.10秒
- Blocked: 約0.326秒

## 状態の持続性

観測列には約775.640秒の無観測区間が1つあります。

この区間を普通の状態遷移として数えず、epoch境界として打ち切ると、

~~~text
Accessible -> Accessible: 38
Accessible -> Blocked:    10
Blocked    -> Accessible:  8
Blocked    -> Blocked:    50
~~~

したがって、

~~~text
P(Blocked next | Accessible) = 0.2083
P(Blocked next | Blocked)    = 0.8621
~~~

となります。

Blockedはこのcapture内ではかなり持続的です。

一方でBlockedは観測周期が短いため、

- 観測回数ベースのBlocked比率: 55.6%
- active wall-clock時間ベース: 約40.2%

となります。

このため、単純な離散Markov chainだけでなく、状態ごとのholding timeを含めたMarkov renewal / semi-Markovな見方が適しています。

## 現在の仮説

今回もっとも直接支持されたのは、

~~~text
429 / blocked response
 -> fast-fail
 -> completion-coupled周期が短くなる
 -> request試行頻度が上がる
~~~

という部分です。

その試行頻度上昇が実際にrate-limit pressureを増やし、

~~~text
試行頻度上昇
 -> pressure上昇
 -> 429
 -> さらにfast-fail
~~~

という正帰還を作っているかは、まだ**因果仮説**です。

内部rate limiterのscopeや実装はHARだけでは分かりません。

## Recovery修正案

修正案の中心は、

**fast-failしたからといって、次のrequest開始時刻まで短くしない**

ことです。

概念的には、

~~~text
next_start =
    max(
        previous_start + minimum_period,
        now + error_backoff
    )
~~~

のようにstart-to-start間隔を守ります。

さらに、

- 429ではbackoff + jitter
- retry budget / circuit breaker
- full snapshotのsingle-flight化
- 安価な再観測を先に行う
- last-known-goodな会話表示を残す
- snapshot整合後にstreamを再接続する
- 1回だけ成功しても即Healthyに戻さないhysteresis

などを提案しています。

詳しくは [docs/recovery-design.md](docs/recovery-design.md) を参照してください。

## 数理モデルと検算

- [数理モデル](docs/model.md)
- [独立再計算・検算](docs/validation.md)
- [方法論](docs/methodology.md)
- [公開summary](data/summary.json)

公開JSONLから再計算できます。

~~~bash
python3 scripts/analyze_public_data.py
~~~

## ロバストMonte Carlo検証

原因モデルを1つに決め打ちせず、

- retryするたびにしか状態が進まないモデル
- 時間経過だけでblocked状態が解けるモデル
- retry自体がpressureを増やす仮想feedbackモデル

の3種類でRecovery方策をstress-testしました。

Accessible周期の30,000回bootstrapでは中央値の95%区間が

~~~text
約10.00秒 ～ 10.99秒
~~~

となりました。

そのため、まず

~~~text
次のrequest開始 >= 前回のrequest開始 + 約10秒
~~~

とする **start-to-start anchor** が、原因を取り違えても壊れにくい
ロバストな中心設計になっています。

CI上の5,000試行referenceでは、10秒anchorは:

- attempt-drivenモデルでrecovery率 99.96%
- latent wall-clockモデルでblocked probe平均 6.85 -> 4.32
- 仮想pressure-feedbackモデルでrecovery率 52.68% -> 69.10%

となりました。

一方、強いexponential backoffはpressure-feedbackモデルでは非常に強いものの、
原因モデルが違う場合は回復検知を大きく遅らせます。

したがって現時点の設計結論は、

> **まずfast-failで試行周期が勝手に短くなることを止める。
> 強いbackoffは追加の証拠がある場合に段階的に使う。**

です。

詳細:

- [Monte Carlo設計検証](docs/monte-carlo.md)
- [Monte Carlo reference JSON](data/monte_carlo_reference.json)
- [再現スクリプト](scripts/monte_carlo_recovery.py)

## プライバシー

原HARは公開していません。

公開データには、private session material、header、本文、会話ID、user/account/project ID、exact URL、query、絶対時刻を含めていません。

詳細は [docs/privacy.md](docs/privacy.md) を参照してください。
