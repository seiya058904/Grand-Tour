'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const {performance} = require('node:perf_hooks');
function loadEngine(file, testMode=true) {
  const html = fs.readFileSync(file,'utf8');
  const storage = new Map();
  const localStorage = {getItem:k=>storage.get(k)??null,setItem:(k,v)=>storage.set(k,String(v)),removeItem:k=>storage.delete(k)};
  const nodes = new Map();
  function node(id) { if (!nodes.has(id)) nodes.set(id,{id,hidden:true,value:'',textContent:'',innerHTML:'',dataset:{},style:{},setAttribute(){},classList:{add(){},remove(){},toggle(){},contains(){return false;}},querySelectorAll(){return []},querySelector(){return null},getClientRects(){return []},append(){},focus(){},addEventListener(){},scrollIntoView(){}}); return nodes.get(id); }
  const document={getElementById:node,querySelector:()=>node('shell'),querySelectorAll:()=>[],createElement:()=>node('new'),activeElement:node('active'),body:node('body'),addEventListener(){},hidden:false};
  const window={addEventListener(){},matchMedia(){return {matches:false}},crypto:require('node:crypto').webcrypto,scrollTo(){},confirm(){return true}};
  const sandbox={window,document,performance,console,localStorage,URLSearchParams,location:{search:testMode?'?test':''},setTimeout,clearTimeout,requestAnimationFrame(){},URL,Blob,Uint32Array,Float64Array};
  vm.createContext(sandbox);
  let src=html.match(/<script>([\s\S]*?)<\/script>/)[1].replace(/^init\(\);$/m,'// Headless engine: skip DOM initialization.');
  src += '\n globalThis.engine={fieldAccounting:typeof fieldAccounting!=="undefined"?fieldAccounting:null,riderRoleLabel:typeof riderRoleLabel!=="undefined"?riderRoleLabel:null,riderAction:typeof riderAction!=="undefined"?riderAction:null,RaceView:typeof RaceView!=="undefined"?RaceView:null,RiderHover:typeof RiderHover!=="undefined"?RiderHover:null,CeremonyStage:typeof CeremonyStage!=="undefined"?CeremonyStage:null,LabelMotion:typeof LabelMotion!=="undefined"?LabelMotion:null,Ceremony:typeof Ceremony!=="undefined"?Ceremony:null,freezePresentation:typeof freezePresentation!=="undefined"?freezePresentation:null,Weather:typeof Weather!=="undefined"?Weather:null,RaceTiming:typeof RaceTiming!=="undefined"?RaceTiming:null,TeamClassification:typeof TeamClassification!=="undefined"?TeamClassification:null,riderAttributes:typeof riderAttributes!=="undefined"?riderAttributes:null,timingDifference:typeof timingDifference!=="undefined"?timingDifference:null,Race,Physics,RIDER_DATA,STAGE_DATA,CONFIG,Classification,Fatigue,Physiology,TimeLimits,SimulationClock,CompactCourse,isRacing,App,Store:()=>Store,normalizeRecord,cloneSave,loadStore,persist,saveActive,TimingView,zeroField,localStorage,storage:undefined, seedForStage:typeof seedForStage==="function"?seedForStage:null,SaveCodec:typeof SaveCodec!=="undefined"?SaveCodec:null, getTesting:()=>typeof TEST_MODE!=="undefined"?TEST_MODE:true};';
  const source = src.replace("globalThis.engine=", "return ");
  sandbox.engine = new Function(...Object.keys(sandbox), source)(...Object.values(sandbox));
  return {engine:sandbox.engine,sandbox,storage,nodes,run:code=>vm.runInContext(code,sandbox)};
}
module.exports={loadEngine};
