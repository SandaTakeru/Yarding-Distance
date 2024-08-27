### Summary
This plugin calculates the “Yarding Distance,” which represents the average distance from a polygon to a point.<br>
Input : Logging Area (Polygon layer), Yarding Point(s) (Point Layer or Click on the map), Dots spacing (value) and Dots Pattern.<br>
Steps : Create dots over the polygon. Measure the lengths from the dots to the Point. Calculate the average of these lengths.<br>
Output : Calculated layers (Yarding Point, Dots in Logging Area, Yarding Graph, and Yarding Distance Label)<br>
The distance calculation is based on the project coordinate system. Euclidean distance or Manhattan distance will be exported.<br>

### 概要
このプラグインは、ポリゴンからポイントまでの平均距離「平均集材距離」を計算します。<br>
入力: 伐区（ポリゴンレイヤー）、集材点（マップキャンバスをクリック）、点群間隔（数値）、点群配置（整列・ランダム）<br>
手順: ポリゴン上に点群を作成します。点群から集材点までの長さを測定します。これらの長さの平均を計算します。<br>
出力: 計算されたレイヤー (集材点、伐区内点群、集材グラフ、平均集材距離ラベル)<br>
距離の計算はプロジェクト座標系に基づいており、ユークリッド距離またはマンハッタン距離を出力できます。<br>
