### Summary
This plugin calculates the “Yarding Distance,” which represents the average distance from a polygon to a point.<br>
Input : Polygon (layer), Point (click on the map), Dot spacing (value), Point<br>
Steps : Create dots over the polygon. Measure the lengths from the dots to the Point. Calculate the average of these lengths.<br>
Output : Calculated layers (yard point, wood dots, transport lines, and labeled polygon)<br>
The distance calculation is based on the project coordinate system, and both the Euclidean distance and the Manhattan distance are provided in the output.<br>

### 概要
このプラグインは、ポリゴンからポイントまでの平均距離「平均集材距離」を計算します。<br>
入力: ポリゴン (レイヤー)、集材点 (マップキャンバスをクリック)、点群間隔 (数値)、点群配置（整列・ランダム）<br>
手順: ポリゴン上に点群を作成します。点群から集材点までの長さを測定します。これらの長さの平均を計算します。<br>
出力: 計算されたレイヤー (集材点、立木点群、輸送グラフ、ラベル付きポリゴン)<br>
距離の計算はプロジェクト座標系に基づいており、ユークリッド距離とマンハッタン距離が出力されます。<br>
