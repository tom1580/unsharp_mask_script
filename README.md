# unsharp_mask_script
Sirilのコマンドでしか操作できないunsharp maskをGUIで操作できるscriptを作成しました。</br>
https://siril.org/docs/ の情報を元にしています。



## 注意点
適用を押して満足する結果ではなかった場合は、Sirilのメインウインドウのundoボタンをクリックして元に戻し、スライダーを調整して再度適用する作業を繰り返す必要があります。

その際、スクリプトのウインドウが隠れてしまうと操作が非常にやりにくいため、ウインドウを常時最前面にする設定にしています。
Siril以外の他のアプリも含めて最前面に表示されてしまいます。

本来はプレビュー機能をつけたかったのですが、sirilpyにはプレビュー機能がサポートされていないため実装できません。

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
