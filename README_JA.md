# ChatGPT Conversation Recovery Dynamics — 日本語概要

これは、ChatGPTで「既存会話が開けない / 429になる / recoveryが完了しない」現象を、匿名化したHAR由来のイベント列から調べる独立ケーススタディです。

**OpenAI内部の根本原因を断定するものではありません。**

## 数理モデルとエビデンス概要

| 層 | 結果 | 扱い |
|---|---|---|
| 観測ペア | 108 = Accessible 48 / Blocked 60 / mixed 0 | 実測・再計算可能 |
| cycle law | `Delta ~= 5.616 + 0.957 S`, `R^2=0.99136` | CIで再計算 |
| Blocked持続 | `P(B_next|B)=0.8621` | epoch境界補正後 |
| 正常周期bootstrap | Accessible中央値 95%区間 **10.002–10.987秒** | 30,000 resamples |
| ロバスト制御 | start-to-startを約10秒未満にしない | Monte Carlo stress-test |
| SNS考古学 | Reddit/HN 15件を保存、default weak-evidence subset 13件 | 歴史資料・弱い観測 |
| 2026反復 | 12の異なる投稿日、185日間に分布 | 発生率ではなく再発記録 |

中核式:

~~~text
Delta_n = S_n + W_n
X ~= 1 / (S + W)

dP/dt = alpha * X(t) - delta * P(t) + xi(t)
Pr(429) = sigmoid(P(t) - Theta(t))
~~~

pressure増加でrejectが速くなり `dS/dP < 0` なら、

~~~text
dX/dP = -S'(P) / (W + S(P))^2 > 0
~~~

となり、局所的な正帰還が成立し得ます。

SNS投稿はこの因果式の証明には使いません。代わりに、
**過去にどの症状の組み合わせが公開観測されていたかという考古学資料と、
単純モデルへの反証constraint** として保存しています。

詳細:

- [数理モデル](docs/model.md)
- [検算](docs/validation.md)
- [Monte Carlo](docs/monte-carlo.md)
- [SNS考古学](docs/external-evidence.md)

## 利用者向け Recovery Helper

会話読み込み失敗、429、空白画面、WebSocket / recovery系エラーで
困っている利用者向けに、**日本語 / English 両対応のlocal-only
Recovery Helper**を追加しました。

~~~text
docs/recovery-helper/index.html
~~~

仕様:

- ChatGPT / OpenAI APIへ自動アクセスしない
- fetch / WebSocket / EventSource / sendBeaconなし
- Cookie / localStorage / sessionStorageなし
- analytics / telemetryなし
- 外部JavaScript・画像・fontなし
- OpenAI公式案内と、この研究由来の提案を明確に区別
- Support向けメモをブラウザ内だけで生成
- UI・切り分け手順・Support memoまで日英切替

つまり、**困っている利用者が切り分けるために、さらにretry trafficを
増やす診断ツールにはしない**設計です。

GitHub Pages用に `/docs` からそのまま公開できる形にしてあります。

詳細:
- [Recovery Helper](docs/recovery-helper/README.md)

GitHub Pagesがまだ有効でない場合だけ、
`Settings -> Pages -> main /docs` の一回の設定が必要です。
現在接続しているGitHub toolからはPages有効化設定そのものは変更できないため、
site本体はdeployment-readyまで仕上げています。

## OpenAI / provider-friendly設計

このrepoの目的を、単なる原因推定ではなく次の形に固定しています。

> **人気サーバーに余計なretry・duplicate snapshot・queue workを増やさず、
> conversation recoveryを安定させる。**

ローカルserver-load simulationでは、base foreground load `rho=0.90` のとき:

| 方策 | retry amplification | recovery payload | recovery reject |
|---|---:|---:|---:|
| naive completion | **18.54x** | 847.4 MiB | 1298.2 |
| Retry-After + jitter | 6.24x | 474.2 MiB | 395.9 |
| single-flight + observe | 4.16x | **366.6 MiB** | 92.8 |
| server-friendly stack | **3.98x** | **366.6 MiB** | **78.3** |

`rho=1.00` では抽象stress model上:

~~~text
naive recovery completion          = 0.8896
server-friendly recovery completion = 1.0000

naive retry amplification          = 62.91x
server-friendly retry amplification = 7.49x
~~~

一方で `rho >= 1` の持続負荷そのものはretry制御では解決できません。

~~~text
base useful work >= service capacity
=> capacity不足
=> 一部をwait / degrade / shedする必要がある
~~~

したがって優先順位は:

~~~text
1. clientでduplicate recoveryを発生させない
2. cheap observation
3. Retry-After + jitter
4. single retry owner
5. bounded queue / early load shedding
6. foreground useful workを保護
7. HTTP/2・HTTP/3はその後のtransport改善
~~~

詳細:

- [provider-friendly congestion control](docs/server-friendly-congestion-control.md)
- [server congestion reference](data/server_congestion_reference.json)
- [responsible testing](RESPONSIBLE_TESTING.md)

production OpenAI endpointへの意図的なload test、rate-limit回避、synthetic retry stormは
このrepoでは推奨しません。過負荷実験はlocal simulationで行います。

## 深掘り検算

今のcycle lawは `R^2 ~= 0.991` ですが、残差にはまだ時系列構造が残っていました。

~~~text
Delta_n = 5.6164 + 0.9566 S_n + u_n
u_n ~= 0.524 u_(n-1) + epsilon_n
~~~

AR(1)を加えると:

~~~text
Delta BIC ~= -29.3
residual SSE 約27.4%減
~~~

さらにpost-completion waitそのものは:

~~~text
phi_W ~= 0.676
~~~

で、単純な「完全固定5.6秒sleep」より、ゆっくり変化するscheduler/controller
stateを持つモデルの方が合います。

解析閾値も検査済みです。

~~~text
pairing window 10–100 ms:
  108 pairs / A48 / B60 / mixed0 で不変

epoch gap 20–600 s:
  AA38 / AB10 / BA8 / BB50 で不変
~~~

また、各active epochで独立にlatency change-pointを探すと、2epochとも
**最初のBlocked観測と完全一致**しました。

history-free A/B Markovが正しい場合に、Blocked直後のAccessible 8回が
8/8すべて再びBlockedになるposterior predictive probabilityは:

~~~text
約 2.31e-5
~~~

です。

詳細:

- [deep trace validation](docs/deep-validation.md)
- [deep validation reference](data/deep_validation_reference.json)

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

## A→B遷移生検とモデル競争

Blockedに入る直前を切り出して再解析すると、現在の成功requestのlatencyよりも
**「そのAccessibleがBlocked直後の一瞬の復帰かどうか」**が強い予測因子でした。

~~~text
Blocked直後の最初のAccessible:
    次もBlocked = 8 / 8

それ以外のAccessible:
    次もBlocked = 2 / 40
~~~

一方向Fisher exact:

~~~text
p ~= 1.19e-7
~~~

したがって、

~~~text
B / Blocked
   -> E / Recovering
   -> H / Healthy
~~~

という中間状態Eを導入します。

観測上は:

~~~text
B -> E -> B : 8
B -> E -> H : 0
~~~

でした。

小標本向けのJeffreys prior + leave-one-out model competitionでも
reentry-historyモデルが最良でした。

~~~text
reentry history LOO log loss ~= 0.199
constant hazard            ~= 0.533

history-aware H/E/B vs first-order A/B:
Delta BIC ~= -28.6
~~~

つまり「200が1回出たら復旧」ではなく、
**最初の成功はprovisional recoveryとして扱う**のが現在のデータに合っています。

詳細:

- [A→B transition biopsy](docs/transition-biopsy.md)
- [transition model competition](docs/transition-model-competition.md)

## 通信プロトコル / recovery経路の再設計

提案経路は:

~~~text
複数window/tabのtrigger
 -> single-flight recovery lease
 -> 軽量なstate/version観測
 -> blockedなら10秒前後のstart-anchor + backoff
 -> 最初の成功でE / Recovering
 -> stable確認
 -> full snapshotを1回だけ取得
 -> atomic reconcile
 -> realtimeを再接続
~~~

通信transport自体は:

~~~text
HTTP/2      基本経路
HTTP/1.1    correctnessを保つfallback
HTTP/3      path migration等のoptional acceleration
WebSocket   realtime notification専用
~~~

とし、conversationの正しさはtransport sessionに依存させません。

5,000試行のrequest-count pressure stress modelでは:

| 経路 | stable recovery | 平均request | 平均payload |
|---|---:|---:|---:|
| completion/context | 20.36% | 38.66 | 28.96 MiB |
| anchor + single-flight | **68.18%** | 11.29 | 13.49 MiB |
| observe -> snapshot | **68.18%** | 11.29 | **4.62 MiB** |

このモデルでは軽量probeもfull snapshotもrequest-count上は同じコストなので、
observe-firstにrate-limit上の有利さを与えていません。
それでもsnapshot materialization量は大幅に減ります。

byte/work-weightedな仮想pressureモデルではobserve-firstが100% recovery /
p95 70秒まで改善しましたが、これは**production limiterの推定値ではなく
stress-test**です。

詳細:

- [transport / recovery-path redesign](docs/transport-recovery-redesign.md)
- [transport simulation reference](data/transport_recovery_reference.json)

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
