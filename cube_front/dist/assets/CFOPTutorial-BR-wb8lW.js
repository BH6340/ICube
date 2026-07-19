import{Bt as e,Et as t,F as n,Ft as r,H as i,I as a,It as o,K as s,Lt as c,Mt as l,Pt as u,Yt as d,Zt as f,_n as p,en as m,ln as h,m as g,p as _,t as v,zt as y}from"./_plugin-vue_export-helper-Dii884fZ.js";import{T as b}from"./index-C-1PbXzW.js";import"./css-BixYjB-z.js";import"./css-7Rigd2Il.js";import"./css-sAqSDmgS2.js";var ee={class:`tutorial-container`},te={class:`tutorial-header`},ne={class:`tutorial-body`},x={class:`steps-sidebar`},S={class:`steps-content`},C={class:`step-header`},w={class:`step-info`},T={class:`info-card`},E={class:`info-icon`},D={class:`info-text`},O={class:`info-card`},k={class:`info-text`},A={class:`info-card`},j={class:`info-text`},M={class:`info-card`},N={class:`info-text`},P={class:`step-content`},F=[`innerHTML`],re={key:0,class:`step-formula`},I={key:0,class:`formula-name`},L={class:`formula-box`},R={key:1,class:`step-tips`},z={key:2,class:`step-advanced`},B=[`innerHTML`],V={class:`step-nav`},H={class:`learning-path`},U=v({__name:`CFOPTutorial`,setup(v){let U=b(),W=h(0),G=[{title:`第一步：十字 (Cross)`,subtitle:`高效规划和执行底层十字`,icon:`🔲`,stats:{algoCount:`0个`,targetTime:`3-5秒`,difficulty:`简单`,goal:`8步以内完成`},content:`
      <p>十字是CFOP的第一步，也是最容易被忽视的一步。目标是在底层完成一个十字，同时规划你的下一个F2L对。</p>
      <h4>十字规划技巧：</h4>
      <ol>
        <li><strong>观察阶段：</strong>在15秒观察期间，找到4个白色棱块的位置</li>
        <li><strong>选择最佳面：</strong>选择需要最少步数的面开始</li>
        <li><strong>高效执行：</strong>目标是8步或更少完成十字</li>
        <li><strong>提前规划：</strong>在完成十字的同时，寻找第一个F2L配对</li>
      </ol>
      <p><strong>关键原则：</strong>十字不需要算法，但需要大量练习来提高规划效率。一个好的十字可以为整个解法节省2-3秒。</p>
    `,formula:[{name:`示例十字公式`,moves:[`F`,`R`,`D`,`R'`,`U'`,`R`]}],tips:[`练习盲拧十字，不看魔方完成十字`,`学习十字规划技巧，目标8步以内`,`在观察期间就开始规划十字`,`完成十字后立即寻找第一个F2L对`],advanced:`
      <p><strong>高级技巧：</strong></p>
      <ul>
        <li><strong>自由十字：</strong>不局限于某一面，选择最优的起始面</li>
        <li><strong>预判十字：</strong>在完成十字时，同时观察第一个F2L配对</li>
        <li><strong>速拧技巧：</strong>学习高效的指法，减少换手次数</li>
      </ul>
    `},{title:`第二步：F2L (First Two Layers)`,subtitle:`配对并插入角块-棱块对`,icon:`🤝`,stats:{algoCount:`41个`,targetTime:`10-12秒`,difficulty:`中等`,goal:`直觉配对`},content:`
      <p>F2L是CFOP中最重要的一步，它将前两层同时解决。通过将角块和棱块配对，然后插入相应位置。</p>
      <h4>F2L基本概念：</h4>
      <ol>
        <li><strong>配对：</strong>找到一个角块和对应的棱块，将它们配对</li>
        <li><strong>插入：</strong>将配对好的角块-棱块对插入前两层</li>
        <li><strong>4对完成：</strong>需要完成4个F2L配对</li>
      </ol>
      <p><strong>学习路径：</strong>建议先从直觉F2L开始，掌握配对技巧后再学习算法。</p>
    `,formula:[{name:`基本F2L插入`,moves:[`U`,`R`,`U'`,`R'`]},{name:`反方向插入`,moves:[`U'`,`L'`,`U`,`L`]},{name:`角块在顶层`,moves:[`R`,`U`,`R'`,`U`,`R`,`U'`,`R'`]},{name:`棱块在顶层`,moves:[`U'`,`R`,`U`,`R'`,`U`,`R`,`U'`,`R'`]}],tips:[`先学习直觉F2L，不要急于背公式`,`练习预判，在完成当前配对时寻找下一个`,`尽量减少转体，学习用左手解决左边的配对`,`熟悉41种F2L情况，但不需要全部记住`],advanced:`
      <p><strong>进阶技巧：</strong></p>
      <ul>
        <li><strong>空槽技巧：</strong>利用已完成的槽位来调整配对</li>
        <li><strong>双F2L：</strong>同时处理两个配对</li>
        <li><strong>预判：</strong>在观察期间定位前两个F2L配对</li>
        <li><strong>指法优化：</strong>学习高效的F2L指法</li>
      </ul>
    `},{title:`第三步：OLL (Orientation of Last Layer)`,subtitle:`一步定向整个顶层`,icon:`🎯`,stats:{algoCount:`57个(两步10个)`,targetTime:`2-3秒`,difficulty:`中等`,goal:`识别所有情况`},content:`
      <p>OLL是CFOP的第三步，目标是将顶层所有块的黄色面朝上。完整OLL有57种情况，但初学者可以从两步OLL开始。</p>
      <h4>两步OLL（适合初学者）：</h4>
      <ol>
        <li><strong>第一步：调整棱块方向（3种情况）</strong>
          <ul>
            <li>点：F R U R' U' F'</li>
            <li>小拐弯：F R U R' U' F'</li>
            <li>一字：F R U R' U' F'</li>
          </ul>
        </li>
        <li><strong>第二步：调整角块方向（7种情况）</strong>
          <ul>
            <li>Sune：R U R' U R U2 R'</li>
            <li>Anti-Sune：R' U' R U' R' U2 R</li>
            <li>其他5种情况</li>
          </ul>
        </li>
      </ol>
      <p><strong>学习建议：</strong>先学习两步OLL（10个算法），达到sub-30秒后再学习完整OLL（57个算法）。</p>
    `,formula:[{name:`Sune`,moves:[`R`,`U`,`R'`,`U`,`R`,`U2`,`R'`]},{name:`Anti-Sune`,moves:[`R'`,`U'`,`R`,`U'`,`R'`,`U2`,`R`]},{name:`十字公式`,moves:[`F`,`R`,`U`,`R'`,`U'`,`F'`]},{name:`T-case`,moves:[`F`,`R`,`U`,`R'`,`U'`,`F'`,`f`,`R`,`U`,`R'`,`U'`,`f'`]},{name:`L-case`,moves:[`F`,`R`,`U`,`R'`,`U'`,`F'`,`R`,`U`,`R'`,`U'`,`R`,`U'`,`R'`,`U`,`R`]}],tips:[`先学习两步OLL，再逐步过渡到完整OLL`,`练习OLL识别，目标0.5秒内识别情况`,`学习多个公式变体，选择适合自己的`,`练习OLL预判，在F2L最后一步就识别OLL情况`],advanced:`
      <p><strong>完整OLL学习建议：</strong></p>
      <ul>
        <li><strong>分组学习：</strong>按形状分组（T、L、S、Pi等）</li>
        <li><strong>公式优化：</strong>学习最短、最高效的公式</li>
        <li><strong>指法练习：</strong>每个公式都要练习到流畅</li>
        <li><strong>视觉识别：</strong>培养快速识别OLL情况的能力</li>
      </ul>
    `},{title:`第四步：PLL (Permutation of Last Layer)`,subtitle:`排列顶层块完成魔方`,icon:`🏁`,stats:{algoCount:`21个(两步6个)`,targetTime:`2-3秒`,difficulty:`中等`,goal:`快速完成排列`},content:`
      <p>PLL是CFOP的最后一步，目标是将顶层所有块排列到正确位置。完整PLL有21种情况，但初学者可以从两步PLL开始。</p>
      <h4>两步PLL（适合初学者）：</h4>
      <ol>
        <li><strong>第一步：排列角块（2种情况）</strong>
          <ul>
            <li>A-perm（顺时针）</li>
            <li>A-perm（逆时针）</li>
          </ul>
        </li>
        <li><strong>第二步：排列棱块（4种情况）</strong>
          <ul>
            <li>U-perm（顺时针）</li>
            <li>U-perm（逆时针）</li>
            <li>H-perm</li>
            <li>Z-perm</li>
          </ul>
        </li>
      </ol>
      <p><strong>学习建议：</strong>先学习两步PLL（6个算法），达到sub-30秒后再学习完整PLL（21个算法）。</p>
    `,formula:[{name:`U-perm (顺时针)`,moves:[`M2`,`U`,`M2`,`U2`,`M2`,`U`,`M2`]},{name:`U-perm (逆时针)`,moves:[`M2`,`U'`,`M2`,`U2`,`M2`,`U'`,`M2`]},{name:`A-perm (顺时针)`,moves:[`R`,`U`,`R'`,`F'`,`R`,`U`,`R'`,`U'`,`R'`,`F`,`R2`,`U'`,`R'`,`U'`]},{name:`A-perm (逆时针)`,moves:[`R'`,`U'`,`R`,`F`,`R'`,`U'`,`R`,`U`,`R`,`F'`,`R2`,`U`,`R`,`U`]},{name:`H-perm`,moves:[`M2`,`U2`,`M2`,`U2`,`M2`]},{name:`Z-perm`,moves:[`M`,`U`,`M2`,`U`,`M2`,`U`,`M`]}],tips:[`先学习两步PLL，再逐步过渡到完整PLL`,`练习PLL识别，目标0.5秒内识别情况`,`学习多个公式变体，选择适合自己的`,`练习PLL预判，在OLL完成前就识别PLL情况`],advanced:`
      <p><strong>完整PLL学习建议：</strong></p>
      <ul>
        <li><strong>分组学习：</strong>按类型分组（Corner、Edge、Corner+Edge）</li>
        <li><strong>公式优化：</strong>学习最短、最高效的公式</li>
        <li><strong>指法练习：</strong>每个公式都要练习到流畅</li>
        <li><strong>视觉识别：</strong>培养快速识别PLL情况的能力</li>
      </ul>
    `}],K=()=>{W.value<G.length-1&&W.value++},q=()=>{W.value>0&&W.value--},J=()=>{U.push(`/`)},Y=()=>{U.push(`/tutorial/oll-essentials`)},X=()=>{U.push(`/tutorial/complete-oll`)};return(h,v)=>{let b=s,U=_,ie=g,Z=n,Q=a,$=i;return d(),c(`div`,ee,[u(`div`,te,[v[1]||=u(`h1`,null,`CFOP方法教程`,-1),v[2]||=u(`p`,{class:`subtitle`},`将你的解题时间减半 - 学习世界冠军使用的方法`,-1),e(b,{onClick:J,icon:`el-icon-arrow-left`,plain:``,size:`small`},{default:m(()=>[...v[0]||=[y(`返回首页`,-1)]]),_:1})]),u(`div`,ne,[u(`div`,x,[e(ie,{active:W.value,"align-center":``,direction:`vertical`},{default:m(()=>[(d(),c(l,null,f(G,(t,n)=>e(U,{key:n,title:t.title},{description:m(()=>[u(`span`,null,p(t.subtitle),1)]),_:2},1032,[`title`])),64))]),_:1},8,[`active`])]),u(`div`,S,[e(t,{name:`fade`,mode:`out-in`},{default:m(()=>[(d(),c(`div`,{key:W.value,class:`step-detail`},[u(`div`,C,[u(`h2`,null,p(G[W.value].title),1),u(`p`,null,p(G[W.value].subtitle),1)]),u(`div`,w,[e(Q,{gutter:20},{default:m(()=>[e(Z,{span:6},{default:m(()=>[u(`div`,T,[u(`span`,E,p(G[W.value].icon),1),u(`span`,D,p(G[W.value].stats.algoCount),1),v[3]||=u(`span`,{class:`info-label`},`算法数`,-1)])]),_:1}),e(Z,{span:6},{default:m(()=>[u(`div`,O,[v[4]||=u(`span`,{class:`info-icon`},`⏱️`,-1),u(`span`,k,p(G[W.value].stats.targetTime),1),v[5]||=u(`span`,{class:`info-label`},`目标时间`,-1)])]),_:1}),e(Z,{span:6},{default:m(()=>[u(`div`,A,[v[6]||=u(`span`,{class:`info-icon`},`📊`,-1),u(`span`,j,p(G[W.value].stats.difficulty),1),v[7]||=u(`span`,{class:`info-label`},`难度`,-1)])]),_:1}),e(Z,{span:6},{default:m(()=>[u(`div`,M,[v[8]||=u(`span`,{class:`info-icon`},`🎯`,-1),u(`span`,N,p(G[W.value].stats.goal),1),v[9]||=u(`span`,{class:`info-label`},`目标`,-1)])]),_:1})]),_:1})]),u(`div`,P,[u(`div`,{innerHTML:G[W.value].content},null,8,F)]),G[W.value].formula&&G[W.value].formula.length>0?(d(),c(`div`,re,[v[10]||=u(`h3`,null,`核心公式`,-1),(d(!0),c(l,null,f(G[W.value].formula,(e,t)=>(d(),c(`div`,{key:t,class:`formula-group`},[e.name?(d(),c(`div`,I,p(e.name),1)):o(``,!0),u(`div`,L,[(d(!0),c(l,null,f(e.moves,(e,t)=>(d(),c(`span`,{key:t,class:`formula-item`},p(e),1))),128))])]))),128))])):o(``,!0),G[W.value].tips?(d(),c(`div`,R,[v[11]||=u(`h3`,null,`练习技巧`,-1),u(`ul`,null,[(d(!0),c(l,null,f(G[W.value].tips,(e,t)=>(d(),c(`li`,{key:t},p(e),1))),128))])])):o(``,!0),G[W.value].advanced?(d(),c(`div`,z,[v[12]||=u(`h3`,null,`进阶学习`,-1),u(`div`,{innerHTML:G[W.value].advanced},null,8,B)])):o(``,!0)]))]),_:1}),u(`div`,V,[e(b,{onClick:q,disabled:W.value===0,icon:`el-icon-arrow-left`},{default:m(()=>[...v[13]||=[y(` 上一步 `,-1)]]),_:1},8,[`disabled`]),W.value<G.length-1?(d(),r(b,{key:0,onClick:K,type:`primary`,icon:`el-icon-arrow-right`},{default:m(()=>[...v[14]||=[y(` 下一步 `,-1)]]),_:1})):(d(),r(b,{key:1,onClick:J,type:`success`,icon:`el-icon-check`},{default:m(()=>[...v[15]||=[y(` 完成学习 `,-1)]]),_:1}))])])]),u(`div`,H,[v[20]||=u(`h2`,null,`学习路径选择`,-1),e(Q,{gutter:20},{default:m(()=>[e(Z,{span:12},{default:m(()=>[e($,{class:`path-card beginner`,onClick:Y},{header:m(()=>[...v[16]||=[u(`div`,{class:`path-header`},[u(`span`,{class:`path-icon`},`🌱`),u(`span`,{class:`path-title`},`初学者路径 - 两步CFOP`),u(`span`,{class:`path-arrow`},`→`)],-1)]]),default:m(()=>[v[17]||=u(`div`,{class:`path-content`},[u(`ul`,null,[u(`li`,null,`✓ 仅需16个算法（相比完整CFOP的78个）`),u(`li`,null,`✓ 1-2周内学会`),u(`li`,null,`✓ 立即达到sub-30秒`),u(`li`,null,`✓ 平滑过渡到完整CFOP`)]),u(`div`,{class:`path-algorithms`},[u(`span`,{class:`alg-item`},`两步OLL: 10个`),u(`span`,{class:`alg-item`},`两步PLL: 6个`)])],-1)]),_:1})]),_:1}),e(Z,{span:12},{default:m(()=>[e($,{class:`path-card advanced`,onClick:X},{header:m(()=>[...v[18]||=[u(`div`,{class:`path-header`},[u(`span`,{class:`path-icon`},`⚡`),u(`span`,{class:`path-title`},`进阶路径 - 完整CFOP`),u(`span`,{class:`path-arrow`},`→`)],-1)]]),default:m(()=>[v[19]||=u(`div`,{class:`path-content`},[u(`ul`,null,[u(`li`,null,`✓ 完整OLL（57种情况）`),u(`li`,null,`✓ 完整PLL（21种情况）`),u(`li`,null,`✓ 达到sub-20秒`),u(`li`,null,`✓ 掌握所有高级技巧`)]),u(`div`,{class:`path-algorithms`},[u(`span`,{class:`alg-item`},`OLL: 57个`),u(`span`,{class:`alg-item`},`PLL: 21个`),u(`span`,{class:`alg-item`},`F2L: 41个`)])],-1)]),_:1})]),_:1})]),_:1})])])}}},[[`__scopeId`,`data-v-c09e499b`]]);export{U as default};