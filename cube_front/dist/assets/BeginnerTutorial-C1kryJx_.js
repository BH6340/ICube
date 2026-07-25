import{Bt as e,C as t,Gt as n,Ht as r,K as i,Lt as a,Sn as o,Vt as s,Wt as c,an as l,en as u,jt as d,m as f,mn as p,nn as m,p as h,t as g,zt as _}from"./_plugin-vue_export-helper-B6HdgdXP.js";import{M as v}from"./index-CnFZdKkJ.js";import"./css-Dz07kxbj.js";var y={class:`tutorial-container`},b={class:`tutorial-header`},x={class:`tutorial-body`},S={class:`steps-sidebar`},C={class:`steps-content`},w={class:`step-header`},T={class:`step-target`},E={key:0,class:`target-image`},D={key:1,class:`target-image placeholder`},O={class:`step-content`},k=[`innerHTML`],A={key:0,class:`step-formula`},j={class:`formula-box`},M={key:1,class:`step-tips`},N={class:`step-nav`},P=g({__name:`BeginnerTutorial`,setup(g){let P=v(),F=p(0),I=[{title:`第一步：对好第一面十字`,subtitle:`建立白色底面十字`,targetImage:`https://aka.doubaocdn.com/s/tmLs1wo1lu`,targetDesc:`目标：白色底面十字，四个侧面的棱与中心块同色`,content:`
      <p>首先我们要对好白色底面的十字。步骤如下：</p>
      <ol>
        <li><strong>做一朵小花：</strong>把四个白色棱块转到黄色中心面，形成一朵白色小花</li>
        <li><strong>转成十字：</strong>把小花的四个白色棱块逐一翻到白色底面</li>
        <li><strong>对齐侧面：</strong>调整顶层，让每个侧面的棱块颜色与中心块一致</li>
      </ol>
      <p><strong>关键点：</strong>对于B和D位置，一步就可以转到顶层；对于A和C位置，转一下侧面就会变到B和D位置。如果有白色棱块挡着，就转一下顶层让个空位。</p>
    `,formula:[[`F`,`R`,`U`,`R'`,`U'`,`F'`]],tips:[`先做小花再转十字，这样更容易`,`侧面颜色不需要对齐时就可以翻下去`,`最后检查每个侧面的棱是否与中心同色`]},{title:`第二步：对好第一面加T字形`,subtitle:`还原白色底面四个角块`,targetImage:`https://aka.doubaocdn.com/s/Gp4Y1wo1lu`,targetDesc:`目标：白色底面完整，四个侧面形成T字形`,content:`
      <p>这一步我们要还原白色底面的四个角块。含有白色的角块只有6种可能位置：</p>
      <ul>
        <li><strong>A和B位置（标准情况）：</strong>白色角块在顶层或中层，只需3步公式</li>
        <li><strong>C、D、E、F位置：</strong>需要先转换成A或B位置</li>
      </ul>
      <p><strong>核心公式（A位置）：</strong>F D F'</p>
      <p><strong>注意：</strong>一定要先把白色角块放在正确的目标位置下面，再做公式。否则T字形不会出来。</p>
    `,formula:[[`F`,`D`,`F'`]],tips:[`先找A或B位置的角块，这样最省事`,`角块要放在正确的目标位置下方`,`做完后检查侧面是否形成T字形`]},{title:`第三步：对好前两层`,subtitle:`还原中间两层的四个棱块`,targetImage:``,targetDesc:`目标：白色底面和中间两层完全还原`,content:`
      <p>这一步我们要还原中间两层的四个棱块。顶层的棱块有两种情况：</p>
      <ul>
        <li><strong>情况1（左）：</strong>棱块在顶层，需要移到左边中间层</li>
        <li><strong>情况2（右）：</strong>棱块在顶层，需要移到右边中间层</li>
      </ul>
      <p><strong>左移公式：</strong>U' L' U L U F U' F'</p>
      <p><strong>右移公式：</strong>U R U' R' U' F' U F</p>
      <p><strong>技巧：</strong>如果中间层的棱块位置不对，可以先用公式把它移到顶层，再用上述公式还原。</p>
    `,formula:[[`U'`,`L'`,`U`,`L`,`U`,`F`,`U'`,`F'`],[`U`,`R`,`U'`,`R'`,`U'`,`F'`,`U`,`F`]],tips:[`先找顶层的棱块，不要着急处理中间层的`,`公式做完后检查中间层是否完整`,`如果找不到可还原的棱块，随便做一次公式就会出现`]},{title:`第四步：在黄色顶面画十字`,subtitle:`还原黄色顶面的四个棱块`,targetImage:`https://aka.doubaocdn.com/s/iB5v1wo1m2`,targetDesc:`目标：黄色顶面形成十字（侧面颜色不需要对齐）`,content:`
      <p>这一步我们要在黄色顶面画出十字。顶面的四个棱块只有4种可能情况：</p>
      <ol>
        <li><strong>点（概率1/8）：</strong>只有中心块是黄色</li>
        <li><strong>小拐弯（概率1/2）：</strong>两个相邻棱块是黄色，要放在右前角</li>
        <li><strong>一字（概率1/4）：</strong>两个相对棱块是黄色，要平行于你</li>
        <li><strong>十字（概率1/8）：</strong>已经完成</li>
      </ol>
      <p><strong>核心公式：</strong>F R U R' U' F'</p>
      <p><strong>用法：</strong>这个公式会按顺序在4种情况中切换。点需要做3次，小拐弯做2次，一字做1次。</p>
    `,formula:[[`F`,`R`,`U`,`R'`,`U'`,`F'`]],tips:[`只看棱块，角块暂时忽略`,`一定要按照正确的方向摆放魔方`,`小拐弯有简便公式可以直接做十字`]},{title:`第五步：对好顶层黄色面`,subtitle:`还原黄色顶面的四个角块朝向`,targetImage:`https://aka.doubaocdn.com/s/E2MA1wo1m2`,targetDesc:`目标：黄色顶面完全还原`,content:`
      <p>这一步我们要调整顶层角块的朝向，让整个黄色顶面还原。顶面四角只有8种情况：</p>
      <ul>
        <li><strong>小鱼1：</strong>鱼头在左后角，侧面三个黄色一顺</li>
        <li><strong>小鱼2：</strong>鱼头在左后角，侧面三个黄色另一顺</li>
      </ul>
      <p><strong>小鱼1公式：</strong>R' U' R U' R' U'2 R</p>
      <p><strong>小鱼2公式：</strong>F U F' U F U2 F'</p>
      <p><strong>技巧：</strong>其他6种情况都可以通过做一次小鱼公式转换成小鱼1或小鱼2。</p>
    `,formula:[[`R'`,`U'`,`R`,`U'`,`R'`,`U'2`,`R`],[`F`,`U`,`F'`,`U`,`F`,`U2`,`F'`]],tips:[`鱼头一定要放在左后角`,`做完小鱼公式后，黄色面会变化`,`最多做2次小鱼公式就能还原`]},{title:`第六步：调整顶层角块位置`,subtitle:`还原顶层四个角块的正确位置`,targetImage:``,targetDesc:`目标：顶层四个角块位置正确（颜色可能不对）`,content:`
      <p>这一步我们要调整顶层四个角块的位置，让它们归位。方法如下：</p>
      <ol>
        <li><strong>找归位的角块：</strong>转动顶层，看看有没有角块的侧面颜色与下面两层一致</li>
        <li><strong>摆好位置：</strong>把归位的角块放在右前角</li>
        <li><strong>做公式：</strong>R2 D2 R' U' R D2 R' U R'</li>
      </ol>
      <p><strong>技巧：</strong>如果没有归位的角块，随便做一次公式就会出现。</p>
    `,formula:[[`R2`,`D2`,`R'`,`U'`,`R`,`D2`,`R'`,`U`,`R'`]],tips:[`先找已经归位的角块`,`归位的角块放在右前角`,`做完公式后检查角块位置`]},{title:`第七步：调整顶层棱块位置`,subtitle:`还原顶层四个棱块的正确位置`,targetImage:``,targetDesc:`目标：魔方完全还原！`,content:`
      <p>最后一步，我们要调整顶层四个棱块的位置，完成魔方还原。方法如下：</p>
      <ol>
        <li><strong>找归位的棱块：</strong>转动顶层，看看有没有棱块的颜色与下面两层一致</li>
        <li><strong>摆好位置：</strong>把归位的面放在后面</li>
        <li><strong>做公式：</strong>F2 U L R' F2 L' R U F2</li>
      </ol>
      <p><strong>技巧：</strong>如果没有归位的棱块，随便做一次公式就会出现。</p>
      <p><strong>恭喜你！</strong>完成这一步后，你的魔方就完全还原了！</p>
    `,formula:[[`F2`,`U`,`L`,`R'`,`F2`,`L'`,`R`,`U`,`F2`]],tips:[`先找已经归位的棱块`,`归位的面放在后面`,`做完公式后检查魔方是否完全还原`,`如果还没还原，再做一次公式`]}],L=()=>{F.value<I.length-1&&F.value++},R=()=>{F.value>0&&F.value--},z=()=>{P.push(`/tutorials`)};return(p,g)=>{let v=i,P=h,B=f,V=t;return u(),r(`div`,y,[_(`div`,b,[g[1]||=_(`h1`,null,`三阶魔方入门教程`,-1),g[2]||=_(`p`,{class:`subtitle`},`层先法 - 7步还原魔方`,-1),n(v,{onClick:z,icon:`el-icon-arrow-left`,plain:``,size:`small`},{default:l(()=>[...g[0]||=[c(`返回首页`,-1)]]),_:1})]),_(`div`,x,[_(`div`,S,[n(B,{active:F.value,"align-center":``,direction:`vertical`},{default:l(()=>[(u(),r(a,null,m(I,(e,t)=>n(P,{key:t,title:e.title},{description:l(()=>[_(`span`,null,o(e.subtitle),1)]),_:2},1032,[`title`])),64))]),_:1},8,[`active`])]),_(`div`,C,[n(d,{name:`fade`,mode:`out-in`},{default:l(()=>[(u(),r(`div`,{key:F.value,class:`step-detail`},[_(`div`,w,[_(`h2`,null,o(I[F.value].title),1),_(`p`,null,o(I[F.value].subtitle),1)]),_(`div`,T,[g[4]||=_(`h3`,null,`目标状态`,-1),I[F.value].targetImage?(u(),r(`div`,E,[n(V,{src:I[F.value].targetImage,fit:`cover`},null,8,[`src`])])):(u(),r(`div`,D,[...g[3]||=[_(`span`,{class:`placeholder-icon`},`🎲`,-1),_(`span`,{class:`placeholder-text`},`目标状态示意图`,-1)]])),_(`p`,null,o(I[F.value].targetDesc),1)]),_(`div`,O,[_(`div`,{innerHTML:I[F.value].content},null,8,k)]),I[F.value].formula&&I[F.value].formula.length>0?(u(),r(`div`,A,[g[5]||=_(`h3`,null,`核心公式`,-1),(u(!0),r(a,null,m(I[F.value].formula,(e,t)=>(u(),r(`div`,{key:t,class:`formula-group`},[_(`div`,j,[(u(!0),r(a,null,m(e,(e,t)=>(u(),r(`span`,{key:t,class:`formula-item`},o(e),1))),128))])]))),128))])):s(``,!0),I[F.value].tips?(u(),r(`div`,M,[g[6]||=_(`h3`,null,`小贴士`,-1),_(`ul`,null,[(u(!0),r(a,null,m(I[F.value].tips,(e,t)=>(u(),r(`li`,{key:t},o(e),1))),128))])])):s(``,!0)]))]),_:1}),_(`div`,N,[n(v,{onClick:R,disabled:F.value===0,icon:`el-icon-arrow-left`},{default:l(()=>[...g[7]||=[c(` 上一步 `,-1)]]),_:1},8,[`disabled`]),F.value<I.length-1?(u(),e(v,{key:0,onClick:L,type:`primary`,icon:`el-icon-arrow-right`},{default:l(()=>[...g[8]||=[c(` 下一步 `,-1)]]),_:1})):(u(),e(v,{key:1,onClick:z,type:`success`,icon:`el-icon-check`},{default:l(()=>[...g[9]||=[c(` 完成学习 `,-1)]]),_:1}))])])])])}}},[[`__scopeId`,`data-v-9c6ddd18`]]);export{P as default};