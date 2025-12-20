# unsharp_mask_script
Sirilのコマンドでしか操作できないunsharp maskをGUIで操作できるscriptを作成しました。  
https://siril.org/docs/ の情報を元にしています。  
<br><br>
# v2.1 update  

## 修正点
1. 表示レスポンスの改善
2. 処理中に画像の拡大縮小を行った際、クラッシュする不具合を軽減<br>
軽減しただけで解決できていないので、スクリプト実行中は画像の拡大縮小を最小限にお願いします。

## 動作環境

siril 1.4.0 で動作を確認しています。
<br>
<br>

# v2 update  

## 修正点
1. tkinerを廃止し、PyQt6に変更
2. プレビュー画面を実装し、V1の注意点を解消しました。  

## 動作環境

siril 1.4.0 RC1 で動作を確認しています。
<br>
<br>

# v1
初版

## 注意点
適用を押して満足する結果ではなかった場合は、Sirilのメインウインドウのundoボタンをクリックして元に戻し、スライダーを調整して再度適用する作業を繰り返す必要があります。

その際、スクリプトのウインドウが隠れてしまうと操作が非常にやりにくいため、ウインドウを常時最前面にする設定にしています。
Siril以外の他のアプリも含めて最前面に表示されてしまいます。

本来はプレビュー機能をつけたかったのですが、実装できていません。

## 動作環境
siril 1.4.0 beta3 で動作を確認しています。

---
# English summary

I've created a GUI script to control Siril's unsharp mask, which is typically only accessible via commands. 
This script is based on information from the Siril documentation.

## Important Notes
If you're not satisfied with the result after applying the unsharp mask, you'll need to undo the action using the "Undo" button in Siril's main window, adjust the sliders in the script, and then reapply.

To make this process easier, I've set the script window to always stay on top. Please note that this means it will appear in front of all other applications, not just Siril.

I originally wanted to add a preview feature, but it couldn't be implemented because sirilpy doesn't support it.

## System Requirements
Siril 1.4.0 beta3.
