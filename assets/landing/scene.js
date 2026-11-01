/* Original procedural light study. No external images, analytics or model calls. */
const zh={skip:'跳至正文',features:'功能',how:'如何使用',start:'开始使用',title:'让合同里的问题，<br>变得清晰。',intro:'从商业合同审查，到条款背后的判例与法律依据。上传材料，在一段对话里继续深入。',explore:'了解功能',regions:'维多利亚州与中国大陆，分别审查。',featureTitle:'从读懂合同，<br>到找到下一步。',featureIntro:'为律师、法务与法学生设计，让文本审查和法律研究衔接起来。',reviewTitle:'审查商业合同',reviewBody:'上传 Word、文字版 PDF 或文本文件，分析法律效力、文本完整性、商业风险与待核实事项，获得表格化发现和修改建议。',reviewDetail:'采购、合作、咨询、技术开发、保密与知识产权等合同。',researchTitle:'围绕条款检索类案',researchBody:'结合上传合同和所选司法区域，检索相关判例与法律规定，查看来源，并区分文本判断与需要进一步核实的法律结论。',researchDetail:'当前检索围绕上传合同展开，需先提供合同材料。',followupTitle:'先审合同，再继续追问',followupBody:'针对某个条款、风险或修改建议继续提问，也可以补充事实，让后续研究延续当前合同的上下文。也可以追问相关案例；选择中国大陆并启用北大法宝后，优先通过北大法宝进行类案检索。',followupDetail:'在页面内查看结果，也可导出审查报告与已采纳的修订。',approachTitle:'带上合同，<br>从一个问题开始。',approachIntro:'选择司法区域，上传合同并输入关注点。收到审查结果后，直接在底部输入框继续追问。',step1:'选择范围',step1body:'维州或中国大陆；可指定审查立场与回答语言。',step2:'上传并提问',step2body:'添加合同及必要补充资料，输入你的问题。',step3:'审查与深入研究',step3body:'阅读风险表格、核对来源，继续追问或导出结果。',privacy:'使用时需配置模型接口密钥。合同及必要资料会发送给模型服务；不保存云端历史。AI 分析供专业复核参考。'};
const en={skip:'Skip to content',features:'Features',how:'How it works',start:'Get started',title:'Bring clarity<br>to every contract.',intro:'Review commercial contracts. Explore the cases and law behind a clause. Upload your documents and take the next question further.',explore:'Explore the features',regions:'Victoria and mainland China, reviewed separately.',featureTitle:'From understanding a contract<br>to deciding what comes next.',featureIntro:'For lawyers, in-house counsel and law students who work across contract review and legal research.',reviewTitle:'Review commercial contracts',reviewBody:'Upload Word, text-based PDF or text files. Assess legal effect, drafting consistency, commercial risk and unresolved facts, with findings and suggested amendments in a table.',reviewDetail:'Procurement, collaboration, consulting, development, confidentiality and IP agreements.',researchTitle:'Research cases around a clause',researchBody:'Use your uploaded contract and selected jurisdiction to research relevant cases and legislation, inspect sources and distinguish drafting judgments from legal conclusions requiring verification.',researchDetail:'Research currently requires an uploaded contract; standalone case research is not yet available.',followupTitle:'Review first. Then ask further.',followupBody:'Ask about a clause, risk or suggested amendment. Add facts and continue the research within the context of the same contract. You can also ask for related cases. With mainland China selected and PKULAW enabled, case research searches PKULAW first.',followupDetail:'Read results in the workspace and export reports or accepted revisions.',approachTitle:'Bring a contract.<br>Start with a question.',approachIntro:'Select a jurisdiction, upload your contract and describe what matters. After the review, continue in the follow-up box at the bottom of the page.',step1:'Choose your scope',step1body:'Victoria or mainland China, with your perspective and answer language.',step2:'Upload and ask',step2body:'Add a contract, relevant supporting materials and your question.',step3:'Review and research further',step3body:'Read the findings, check sources, ask a follow-up or export your work.',privacy:'A model API key is required. Contracts and necessary materials are sent to the model provider. No cloud history is stored. AI analysis requires professional review.'};

Object.assign(zh,{
 settingsNav:'设置',settingsTitle:'让审查，<br>更贴合你的需要。',
 settingsIntro:'进入工作台后，点击左侧栏底部的“设置”，选择语言与审查立场，再连接自己的模型账户。',
 settingsNote:'界面语言与回答语言分别设置；上传文件的原文不会随界面语言改变。',
 settingUiTitle:'界面语言',settingUiBody:'选择中文或英文，切换导航、按钮和操作提示。',
 settingOutputTitle:'输出语言',settingOutputBody:'跟随问题语言，或指定中文、英文、中英双语。',
 settingStanceTitle:'审查立场',settingStanceBody:'填写你代表的交易方，例如采购方、供应商或顾问；未指定时中立审查。',
 settingKeyTitle:'你的 API Key',settingKeyBody:'展开“模型与接入”，输入自己的 API Key。密钥仅用于当前会话，可通过“测试分析模型连接”检查接入。',
 settingModelTitle:'模型选择',settingModelBody:'分别选择分析模型与联网模型：gpt-6-luna 或 gpt-6.1-sol。实际可用性取决于接口和账户权限。'
});
Object.assign(en,{
 settingsNav:'Settings',settingsTitle:'Make the review<br>work for you.',
 settingsIntro:'In the workspace, open Settings at the bottom of the left sidebar. Choose your languages and review perspective, then connect your own model account.',
 settingsNote:'Interface and answer languages are set separately. Changing the interface language leaves your original documents unchanged.',
 settingUiTitle:'Interface language',settingUiBody:'Choose English or Chinese for navigation, buttons and instructions.',
 settingOutputTitle:'Answer language',settingOutputBody:'Follow the language of your question, or choose English, Chinese or both.',
 settingStanceTitle:'Your perspective',settingStanceBody:'Tell the agent whom you represent, such as a buyer, supplier or consultant. If no perspective is specified, the review is neutral.',
 settingKeyTitle:'Your API key',settingKeyBody:'Expand Model & connection and enter your own API key, used only for the current session. Use Test analysis model connection to check the connection.',
 settingModelTitle:'Model selection',settingModelBody:'Choose an analysis model and a search model separately: gpt-6-luna or gpt-6.1-sol. Availability depends on your endpoint and account permissions.'
});
let english=true,nonce=0;
const send=(type,data={})=>parent.postMessage({isStreamlitMessage:true,type,...data},'*');
function event(action){send('streamlit:setComponentValue',{value:{action,language:english?'English':'中文',nonce:Date.now()+nonce++},dataType:'json'});}
function localise(){const copy=english?en:zh;document.documentElement.lang=english?'en':'zh-CN';document.querySelectorAll('[data-copy]').forEach(e=>{const text=copy[e.dataset.copy];if(e.dataset.copy==='title'||e.dataset.copy.endsWith('Title'))e.innerHTML=text;else e.textContent=text;});document.getElementById('locale').textContent=english?'中文':'English';resetInteractions();resizeFrame();}
function resizeFrame(){send('streamlit:setFrameHeight',{height:Math.ceil(document.documentElement.scrollHeight)});}
document.querySelectorAll('.start').forEach(e=>e.addEventListener('click',()=>event('start')));
document.getElementById('locale').addEventListener('click',()=>{english=!english;localise();event('language');});
window.addEventListener('message',e=>{if(e.source!==parent||e.data?.type!=='streamlit:render')return;english=e.data.args.language==='English';localise();requestFrame();});
new ResizeObserver(resizeFrame).observe(document.body);
// Pointer-only effects: one scheduled frame per move; no continuous animation loop.
const finePointer=matchMedia('(hover: hover) and (pointer: fine)');
const magnets=Array.from(document.querySelectorAll('.magnetic-wrap'));
const spotlightCards=Array.from(document.querySelectorAll('.feature, .settings-panel'));
let pointerFrame=0,pointer=null,spotFrame=0,spot=null;
function resetInteractions(){
 cancelAnimationFrame(pointerFrame);cancelAnimationFrame(spotFrame);pointerFrame=0;spotFrame=0;pointer=null;spot=null;
 magnets.forEach(w=>{w.firstElementChild.style.removeProperty('--mag-x');w.firstElementChild.style.removeProperty('--mag-y');});
 spotlightCards.forEach(f=>f.classList.remove('is-lit'));
}
document.addEventListener('pointermove',e=>{
 if(!finePointer.matches||e.pointerType!=='mouse')return;
 pointer={x:e.clientX,y:e.clientY};if(pointerFrame)return;
 pointerFrame=requestAnimationFrame(()=>{pointerFrame=0;
  magnets.forEach(w=>{const b=w.firstElementChild,r=w.getBoundingClientRect();let x=0,y=0;
   const dx=pointer.x-r.left-r.width/2,dy=pointer.y-r.top-r.height/2;
   const outside=Math.hypot(Math.max(Math.abs(dx)-r.width/2,0),Math.max(Math.abs(dy)-r.height/2,0));
   if(outside<64&&!b.matches(':focus-visible')){const pull=1-outside/64;x=Math.max(-12,Math.min(12,dx*.18*pull));y=Math.max(-8,Math.min(8,dy*.18*pull));}
   b.style.setProperty('--mag-x',x+'px');b.style.setProperty('--mag-y',y+'px');
  });
 });
},{passive:true});
spotlightCards.forEach(f=>{
 f.addEventListener('pointermove',e=>{if(!finePointer.matches||e.pointerType!=='mouse')return;
  spot={element:f,x:e.clientX,y:e.clientY};if(spotFrame)return;
  spotFrame=requestAnimationFrame(()=>{spotFrame=0;const r=spot.element.getBoundingClientRect();
   spot.element.style.setProperty('--spot-x',(spot.x-r.left)+'px');spot.element.style.setProperty('--spot-y',(spot.y-r.top)+'px');spot.element.classList.add('is-lit');});
 },{passive:true});
 f.addEventListener('pointerleave',()=>{f.classList.remove('is-lit');if(spot?.element===f){cancelAnimationFrame(spotFrame);spotFrame=0;spot=null;}});
});
document.addEventListener('mouseleave',resetInteractions);
document.addEventListener('focusin',e=>{if(e.target.matches(':focus-visible'))resetInteractions();});
finePointer.addEventListener('change',resetInteractions);
// A low-resolution WebGL caustic field. Static colour is the no-WebGL fallback.
const canvas=document.getElementById('water'),gl=canvas.getContext('webgl',{alpha:false,antialias:false,depth:false,powerPreference:'low-power'});
let framePending=false,program,startTime=performance.now(),lastTime=0,visible=true;
function requestFrame(){if(gl&&program&&!framePending&&visible&&!document.hidden){framePending=true;requestAnimationFrame(draw);}}
function draw(now){framePending=false;if(!gl||!program)return;const w=Math.min(1000,canvas.clientWidth),h=Math.round(w*canvas.clientHeight/canvas.clientWidth);if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;gl.viewport(0,0,w,h);}lastTime=(now-startTime)/1000;gl.uniform2f(gl.getUniformLocation(program,'resolution'),w,h);gl.uniform1f(gl.getUniformLocation(program,'time'),lastTime);gl.drawArrays(gl.TRIANGLES,0,6);requestFrame();}
if(gl){try{const vertex='attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}';const fragment=`precision mediump float;uniform vec2 resolution;uniform float time;uniform vec3 low;uniform vec3 high;uniform vec3 pale;uniform vec3 lightColor;
void main(){vec2 uv=gl_FragCoord.xy/resolution;vec2 p=(uv-.5)*vec2(resolution.x/resolution.y,1.)*5.;float t=time*.11;
vec2 q=p;q+=.45*vec2(sin(p.y*1.7+t)+sin(p.x*1.2-t),cos(p.x*1.6-t)+sin(p.y+t));
float a=sin(q.x*2.7+sin(q.y*2.2+t)*1.6+t);float b=sin(q.y*2.9+cos(q.x*1.8-t)*1.5-t);
float light=pow(max(0.,1.-abs(a+b)*.83),15.);float second=pow(max(0.,1.-abs(a-b)*.95),22.);
vec3 water=mix(low,high,uv.y);water+=lightColor*(light+second*.55);
float focus=smoothstep(.05,.85,abs(uv.x-.5)*1.9);water=mix(pale,water,.50+.4*focus);gl_FragColor=vec4(water,1.);}`;
function shader(type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error('shader unavailable');return s;}
program=gl.createProgram();gl.attachShader(program,shader(gl.VERTEX_SHADER,vertex));gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fragment));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('link unavailable');gl.useProgram(program);
const tokens=getComputedStyle(document.documentElement);for(const [uniform,token] of [['low','--water-low'],['high','--water-high'],['pale','--water-pale'],['lightColor','--water-light']]){const hex=tokens.getPropertyValue(token).trim().slice(1);gl.uniform3f(gl.getUniformLocation(program,uniform),parseInt(hex.slice(0,2),16)/255,parseInt(hex.slice(2,4),16)/255,parseInt(hex.slice(4,6),16)/255);}const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);const position=gl.getAttribLocation(program,'p');gl.enableVertexAttribArray(position);gl.vertexAttribPointer(position,2,gl.FLOAT,false,0,0);draw(performance.now());}catch{program=null;canvas.style.display='none';}}
new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;requestFrame();}).observe(canvas);
document.addEventListener('visibilitychange',requestFrame);window.addEventListener('resize',()=>{requestFrame();});
canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();program=null;canvas.style.display='none';});
send('streamlit:componentReady',{apiVersion:1});localise();
