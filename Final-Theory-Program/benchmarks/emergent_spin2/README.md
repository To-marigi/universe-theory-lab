# Emergent Spin-2 Gate v0.1

このベンチは、候補模型から導いた応答と、既知のSpin-2運動学を検査する独立oracleを
分離する。

## 独立陽性対照

実行コードは次を検査する。

1. D=4の非零Euclidean運動量におけるBarnes-Rivers Spin-2射影子
   - 冪等性
   - 横波性
   - 無跡性
   - 添字対称性
   - off-shell射影子rank 5
2. D=4の固定null運動量に対するplus/cross偏極
   - null運動量
   - 横波・無跡
   - 直交規格化
   - 独立な物理偏極2個
3. 線形化Einstein/Fierz-Pauli作用
   - 4つの線形ゲージ方向が運動演算子の核
   - 線形化Bianchi/Ward恒等式

off-shell rank 5とon-shell 2偏極は異なる量であり、同一視しない。

## 候補の合格条件

候補自身が次をすべて出力した場合だけ `SPIN2_GATE_PASS` を許可する。

- 導出された二点応答
- `1/(k^2+i0)` の質量ゼロ極
- Spin-2残差
- D=4で物理偏極2個
- Ward恒等式
- scalar/vector ghost不在
- 保存された全エネルギー運動量への単一結合
- 粗視化スケール安定性
- 未使用因果構造での再現

陽性対照を候補の二点関数として代入することはmutation failureである。

## v0.1判定

`causal_information_v1` は候補由来の応答をまだ持たない。したがって陽性対照が
PASSしても候補判定は `SPIN2_NOT_FOUND`、全体判定は `FINAL_THEORY_OPEN` である。
