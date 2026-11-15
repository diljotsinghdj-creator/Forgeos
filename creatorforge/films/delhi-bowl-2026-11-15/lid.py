"""The lid: real particle physics (Rapier). Left: an ordinary day, warm air near the ground, smoke rises and spreads.
Right: an inversion, a warm layer above acts as a lid and the smoke piles up underneath. Labelled illustrative."""
from pathlib import Path
from physics_base import HEAD, TAIL
D = Path(__file__).resolve().parent
BODY = r"""
S.background=new THREE.Color('#EDE7DA');
W.gravity={x:0,y:2.2,z:0};            // smoke is buoyant: it drifts up
fixedBox(0,-.1,0,40,.1,6,'#CFC5B2');
const lidY=4.2;
// right side: the lid (warm layer) as a glowing amber slab, a real collider
W.createCollider(RAPIER.ColliderDesc.cuboid(6,.25,3).setTranslation(7,lidY,0));
const lid=mesh(new THREE.BoxGeometry(12,.5,6),'#F2A541',{transparent:true,opacity:.55,emissive:'#F2A541',emissiveIntensity:.35});lid.position.set(7,lidY,0);
for(const x of [-13,1,13]) W.createCollider(RAPIER.ColliderDesc.cuboid(.1,8,3).setTranslation(x,7,0));   // invisible walls keep each side apart
W.createCollider(RAPIER.ColliderDesc.cuboid(14,.1,.1).setTranslation(0,4,3.1));W.createCollider(RAPIER.ColliderDesc.cuboid(14,.1,.1).setTranslation(0,4,-3.1));
for(const z of [-3,3])W.createCollider(RAPIER.ColliderDesc.cuboid(14,10,.1).setTranslation(0,8,z));
// chimneys / sources
for(const x of [-7,7]){const m=mesh(new THREE.CylinderGeometry(.35,.45,1.4,20),'#3A3A3A');m.position.set(x,.7,0)}
const g=new THREE.SphereGeometry(.16,12,10);
for(let step=0;step<STEPS;step++){
  if(step%2===0) for(const x of [-7,7]){const b=W.createRigidBody(RAPIER.RigidBodyDesc.dynamic().setTranslation(x+(Math.random()-.5)*.3,1.6,(Math.random()-.5)*.3).setLinearDamping(1.2).setLinvel((Math.random()-.5)*(x<0?3.2:1.2),1.5,(Math.random()-.5)*1.2));
    W.createCollider(RAPIER.ColliderDesc.ball(.16).setRestitution(.1).setFriction(.05).setDensity(.3),b);
    const m=mesh(g,x<0?'#8B8680':'#6E6760',{roughness:1});m.castShadow=false;pairs.push([b,m])}
  W.step()}
for(const [b,m] of pairs){const t=b.translation();if(t.y>10.5)m.visible=false}
const cam=new THREE.PerspectiveCamera(32,1920/1080,.1,200);cam.position.set(0,7.5,26);cam.lookAt(0,6.4,0);
const OVER=`<div style="left:1080px;top:70px;width:780px"><div style="font:400 130px/0.9 Anton;color:#141414">THE LID</div>
<div style="font:400 46px ISerif;color:#141414;margin-top:6px">warm air on top keeps the smoke down</div></div>
<div style="left:640px;top:330px;width:360px"><div style="font:500 20px Plex;letter-spacing:4px;color:#444">AN ORDINARY DAY</div><div style="font:700 40px Caveat;color:#2457C5">smoke rises and spreads</div></div>
<div style="left:1080px;top:430px;width:700px"><div style="font:500 20px Plex;letter-spacing:4px;color:#7A2A20">A NOVEMBER INVERSION</div><div style="font:700 40px Caveat;color:#C8312B">a warm layer above acts as a lid</div></div>
<div style="left:24px;bottom:14px;font:500 12px Plex;color:rgba(0,0,0,.45)">ILLUSTRATIVE: REAL PHYSICS SIMULATION (RAPIER) OF BUOYANT PARTICLES · THE LID: NASA EARTH OBSERVATORY, 3 NOV 2024</div>`;
"""
if __name__ == "__main__":
    (D / "html" / "04_the_lid.html").write_text(HEAD + "const STEPS=900;\n" + BODY + TAIL)
