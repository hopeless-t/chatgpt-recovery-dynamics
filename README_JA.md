# ChatGPT Conversation Recovery Dynamics — 日本語概要

これは、ChatGPTで「既存会話が開けない / 429になる / recoveryが完了しない」現象を、匿名化したHAR由来のイベント列から調べる独立ケーススタディです。

**OpenAI内部の根本原因を断定するものではありません。**

## このcaptureで見えたこと

大きい方のHARだけを重複排除して解析しました。

- recovery関連イベント: 253
- `stream status` と `conversation snapshot` の同時観測ペア: 108
- Accessible: 48
- Blocked: 60
- 混合ペア: 0

Blockedでは、

- snapshot: HTTP 429
- stream status: HTTP responseなし

が同時に観測されました。

観測間隔中央値は:

- Accessible: 10.272秒
- Blocked: 5.998秒

snapshot latency中央値は:

- Accessible: 約5.10秒
- Blocked: 約0.326秒

つまりblocked側では、失敗がかなり速く返り、次の観測/再試行周期も短くなっています。

## 仮説

単純に

`429 -> recovery failure`

だけではなく、

`recovery/observability低下 -> retry増幅 -> request pressure増加 -> 429 -> さらにrecovery困難`

という正帰還が存在する可能性を検討しています。

これはDCS（dissociated control states）というシステム上の見方を使っています。

ここでのDCSは、ひとつのシステムを単純な「正常/故障」に潰さず、

- canonical stateの存在
- snapshot accessibility
- stream observability
- recovery attachment
- pressure
- user-visible utility

を別々の状態変数として扱う、という意味です。

## プライバシー

原HARは公開していません。

公開データには、cookie、authorization、header、本文、会話ID、user/account/project ID、exact URL、query、絶対時刻を含めていません。

詳細は英語READMEと `docs/privacy.md` を参照してください。
