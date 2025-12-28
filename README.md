# VRM-Fur-Shell-Texturing
Blender plug-in to automatically add fake fur, AKA shell texturing, to your VRM models. Select materials to use it on and it'll do it easily. It works for hair, fur, and more, and was made for VRoid models, but should work on any VRM model in theory.
Blenderプラグインで、VRMモデルにフェイクファー（別名シェルテクスチャリング）を自動追加。適用するマテリアルを選択するだけで簡単に処理できます。髪や毛皮などに対応し、VRoidモデル向けに作成されましたが、理論上はあらゆるVRMモデルで動作するはずです。

<img width="3172" height="2018" alt="image" src="https://github.com/user-attachments/assets/13c12894-746c-4505-aeec-01921c5ae37d" />

## Usage
- Make sure you have the VRM Add-on for Blender installed: https://vrm-addon-for-blender.info/en-us/
- Load your VRM model in Blender with the addon.
- Open the plug-in panel with N (by default), and find the VRM tab and press it.
- Inside this tab, at the very bottom, you'll find VRM Hair Shell Texturing (MToon). Expand it if it isn't.
- Select with object mode the mesh you want to add fur/hair shell textures to.
- Press "Refresh Material List" to populate the list of materials on the mesh.
  - If there are materials you do not want to be affected (accessories, solid objects, etc), untick the checkbox for the program to ignore it.
- Set the Layers to something like 3 to start with. The more layers, the more polygons you'll be adding to your model.
- Select the texture shape for the fur: vertical for well-tamed hair, random for... well, random.
- (There are also taper options but you should mess with them if you're not satisfied with the shape after trying it out)
- Press the Add Shell Texturing (MToon) button, and it'll be added.
- If your materials had outlines enabled, you can press the Turn Off Outlines button to disable MToon outlines on the selected materials in the list. They tend to conflict visually but might not show in Blender, so if you've got visual issues in another software, press this button to fix that.
- If you're not satisfied with the spacing of each layer, you can go into the Modifiers tab (wrench icon) and change the values in real time.
- Export the model as a VRM and it should work. Some software might require some small adjustments on the shell textures material properties.

For RPG Developer Bakin users: it works well. You might need to configure some of the material properties in the engine regarding how it handles lighting.

Special thanks to Grok for helping me make this blender plug-in.

## 使用方法
- Blender用VRMアドオンがインストールされていることを確認してください: https://vrm-addon-for-blender.info/en-us/
- アドオンを使用してBlenderにVRMモデルを読み込みます。
- Nキー（デフォルト）でプラグインパネルを開き、VRMタブを見つけてクリックします。
- このタブの最下部にある「VRM Hair Shell Texturing (MToon)」を探します（展開されていない場合は展開してください）。
- オブジェクトモードで、毛皮/ヘアシェルテクスチャを追加したいメッシュを選択します。
- 「Refresh Material List」を押して、メッシュ上のマテリアルリストを反映させます。
  - 影響を受けたくないマテリアル（アクセサリーや固体オブジェクトなど）がある場合は、チェックボックスを外してプログラムに無視させます。
- レイヤー数を最初は3程度に設定します。レイヤー数が多いほど、モデルに追加されるポリゴン数も増えます。
- 毛並みのテクスチャ形状を選択します：垂直は整った髪、ランダムは…まあ、ランダムな感じになります。
- （テーパーオプションもありますが、試してみて形状に満足できない場合は調整してみてください）
- 「Add Shell Texturing (MToon)」ボタンを押すと追加されます。
- マテリアルにアウトラインが有効になっている場合、「アウトラインを無効化」ボタンを押すと、リストで選択したマテリアルのMToonアウトラインを無効化できます。視覚的に干渉する傾向がありますが、Blender上では表示されない場合があります。他のソフトウェアで視覚的な問題が発生している場合は、このボタンを押して修正してください。
- 各レイヤーの間隔に満足できない場合は、「モディファイア」タブ（レンチアイコン）を開き、リアルタイムで値を変更できます。
- モデルをVRM形式でエクスポートすれば動作するはずです。一部のソフトウェアでは、シェルのテクスチャマテリアルプロパティに微調整が必要な場合があります。

RPG開発ツール「Bakin」ユーザー向け：正常に動作します。エンジンのマテリアルプロパティで、ライティング処理に関する設定を調整する必要があるかもしれません。

このBlenderプラグイン作成にご協力いただいたGrok氏に、特に感謝申し上げます。
