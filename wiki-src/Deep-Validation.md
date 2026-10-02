# Deep Validation

The high-R² timing law still leaves structured residual memory.

```text
Delta_n = 5.6164 + 0.9566 S_n + u_n
u_n ~= 0.524 u_(n-1) + epsilon_n
```

Adding AR(1) residual memory improves BIC by about 29.3 points and reduces residual SSE by about 27.4%.

Other checks:

- 108/48/60/0 pairing stable from 10–100 ms
- transition matrix stable for epoch gaps 20–600 s
- cycle law cross-predicts the other active epoch at ~0.25–0.26 s RMSE
- service-time change point equals first Blocked observation in both epochs
- history-free A/B model gives ~2.31e-5 posterior-predictive probability to the observed 8/8 rebound

Full audit: [deep validation](https://github.com/hopeless-t/chatgpt-recovery-dynamics/blob/main/docs/deep-validation.md)