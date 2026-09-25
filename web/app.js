const levelInfo = {
  1: { label: "Very low suspicion", description: "Normal CT or findings considered non-infectious." },
  2: { label: "Low suspicion", description: "Pulmonary findings typical of infection other than COVID-19." },
  3: { label: "Equivocal", description: "Indeterminate findings compatible with COVID-19 and other causes." },
  4: { label: "High suspicion", description: "Suspicious COVID-19 pattern that is not fully typical for CO-RADS 5." },
  5: { label: "Very high suspicion", description: "Typical bilateral multifocal peripheral/subpleural COVID-19 pattern." },
  6: { label: "RT-PCR confirmed", description: "SARS-CoV-2 infection reported as confirmed by RT-PCR." }
};
const byId = (id) => document.getElementById(id);
const checked = (id) => byId(id).checked;
function isCorads5(f) { return f.ggo && f.peripheral && f.bilateral && f.multifocal && !f.unilateral; }
function isCorads4(f) { if (!f.ggo || isCorads5(f)) return false; return [f.peripheral,f.posterior,f.bilateral,f.multifocal,f.crazyPaving,f.posteriorConsolidation].filter(Boolean).length >= 2; }
function isCorads2(f) { return f.treeInBud || f.cavitation || (f.consolidation && !f.ggo && !f.crazyPaving); }
function classify(f) { if (f.pcrPositive) return 6; if (isCorads5(f)) return 5; if (isCorads4(f)) return 4; if (isCorads2(f)) return 2; if (f.ggo || f.diffuseBilateralGgo || f.crazyPaving || f.consolidation) return 3; return 1; }
function collectFindings() { return { ggo:checked("ggo"), peripheral:checked("peripheral"), posterior:checked("posterior"), bilateral:checked("bilateral"), multifocal:checked("multifocal"), crazyPaving:checked("crazyPaving"), consolidation:checked("consolidation"), posteriorConsolidation:checked("posteriorConsolidation"), treeInBud:checked("treeInBud"), cavitation:checked("cavitation"), lymphadenopathy:checked("lymphadenopathy"), pleuralEffusion:checked("pleuralEffusion"), diffuseBilateralGgo:checked("diffuseBilateralGgo"), unilateral:checked("unilateral"), pcrPositive:checked("pcrPositive") }; }
function severityScore() { return ["ru","rm","rl","lu","ll"].map((id)=>Number(byId(id).value)).reduce((sum,value)=>sum+value,0); }
function featureList(f) { const a=[]; if(f.ggo)a.push("ground-glass opacities"); if(f.peripheral)a.push("peripheral/subpleural distribution"); if(f.posterior)a.push("posterior distribution"); if(f.bilateral)a.push("bilateral involvement"); if(f.multifocal)a.push("multifocal involvement"); if(f.crazyPaving)a.push("crazy paving"); if(f.consolidation)a.push("consolidation"); if(f.treeInBud)a.push("tree-in-bud"); if(f.cavitation)a.push("cavitation"); if(f.lymphadenopathy)a.push("lymphadenopathy"); if(f.pleuralEffusion)a.push("pleural effusion"); return a; }
function renderResult(level,score,f) { const info=levelInfo[level]; const features=featureList(f); const markup=features.length ? `<ul>${features.map((x)=>`<li>${x}</li>`).join("")}</ul>` : "<p>No modeled pulmonary opacity features selected.</p>"; byId("result").innerHTML=`<div class="result-main">CO-RADS ${level} — ${info.label}</div><p>${info.description}</p><div class="score">CT severity score: ${score}/25</div><h3>Selected findings</h3>${markup}<p class="muted">This output is a simplified rule-based approximation and requires radiologist review.</p>`; }
function initializeLobeSelects() { for(const id of ["ru","rm","rl","lu","ll"]) { const select=byId(id); for(let value=0; value<=5; value+=1) { const option=document.createElement("option"); option.value=String(value); option.textContent=String(value); select.appendChild(option); } } }
byId("assessment-form").addEventListener("submit",(event)=>{ event.preventDefault(); const findings=collectFindings(); renderResult(classify(findings),severityScore(),findings); });
initializeLobeSelects();
