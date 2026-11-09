// CreatorForge drawn illustrations: flat editorial objects (ink outline, flat colour, halftone shading, one accent).
// Each entry: [width, height, draw(g, acc)] in its own design box; callers scale the group. Generic objects only:
// no real logos, flags or currency designs.
(function(){
const INK='#1C1C1C', STEEL='#5B6770', PAPER='#EFE9DC', RED='#C8402C', NAVY='#1E2B4A', CBOX=['#C8402C','#1E5C78','#E0A030','#2E7D5B','#7A3E8C','#D86A2A'];
const o=(w)=>({color:INK,width:w||1.6,linejoin:'round',linecap:'round'});
function dots(g){const r=g.root();if(!r.__ildots)r.__ildots=r.pattern(5,5,a=>a.circle(2.3).center(2.5,2.5).fill('#000').opacity(.24));return r.__ildots}
function shade(g,el){el.fill(dots(g)).stroke({width:0});return el}   // the shape becomes a halftone shadow
function poly(g,pts,fill,w){return g.polygon(pts.map(p=>p.join(',')).join(' ')).fill(fill).stroke(o(w))}
const I={};
I.container=[120,52,(g,acc)=>{const b=g.rect(120,52).fill(RED).stroke(o(2));for(let x=8;x<120;x+=8)g.line(x,4,x,48).stroke({color:'#00000040',width:2});
  g.rect(120,52).fill('none').stroke(o(2.2));shade(g,g.rect(120,18).move(0,34));g.rect(14,30).move(98,11).fill('none').stroke(o(1.2))}];
I.ship=[300,140,(g,acc)=>{ // container ship, side view
  for(let r=0;r<3;r++)for(let c=0;c<9;c++){if(r===2&&(c<2||c>6))continue;g.rect(22,14).move(52+c*23,46-r*15).fill(CBOX[(r*3+c*2)%CBOX.length]).stroke(o(1.1))}
  g.rect(26,40).move(256,20).fill(PAPER).stroke(o(1.4));g.rect(18,6).move(260,26).fill(NAVY);g.rect(6,16).move(270,4).fill(INK);
  poly(g,[[8,62],[292,62],[278,104],[30,104]],NAVY,2);poly(g,[[30,104],[278,104],[272,112],[38,112]],RED,1.6);
  shade(g,poly(g,[[150,62],[292,62],[278,104],[150,104]],'none',0));g.line(8,62,292,62).stroke(o(2.2));
  for(let k=0;k<5;k++)g.path(`M${10+k*60} 124 q 15 -8 30 0 t 30 0`).fill('none').stroke({color:'#7FA6B8',width:2.2,linecap:'round'})}];
I.crane=[160,220,(g,acc)=>{ // ship-to-shore gantry crane
  const y=acc;poly(g,[[30,220],[42,220],[60,70],[52,70]],'#D86A2A',1.4);poly(g,[[100,220],[112,220],[104,70],[96,70]],'#D86A2A',1.4);
  g.rect(150,12).move(0,60).fill('#D86A2A').stroke(o(1.6));for(let x=6;x<150;x+=12)g.line(x,60,x+6,72).stroke(o(1));
  g.rect(70,8).move(40,150).fill('#D86A2A').stroke(o(1.4));g.rect(20,16).move(60,72).fill(PAPER).stroke(o(1.2));
  g.line(70,88,70,140).stroke(o(1.2));g.rect(36,18).move(52,140).fill(CBOX[1]).stroke(o(1.2));g.line(30,60,150,20).stroke(o(1.4));g.line(52,60,52,20).stroke(o(1.4))}];
I.truck=[220,110,(g,acc)=>{g.rect(140,62).move(4,18).fill(CBOX[1]).stroke(o(2));shade(g,g.rect(140,20).move(4,60));
  poly(g,[[146,40],[196,40],[214,62],[214,82],[146,82]],RED,2);g.rect(26,16).move(160,46).fill('#CFE3EA').stroke(o(1.4));
  g.rect(212,6).move(4,82).fill(INK);[34,62,170,198].forEach(x=>{g.circle(26).center(x,92).fill(INK);g.circle(10).center(x,92).fill('#9AA4AA')})}];
I.factory=[260,170,(g,acc)=>{g.rect(220,90).move(20,80).fill('#B65A3A').stroke(o(2));for(let k=0;k<4;k++)poly(g,[[20+k*55,80],[75+k*55,80],[75+k*55,52]],'#9E4B30',1.6);
  [[40,10],[80,26]].forEach(([x,y])=>{g.rect(18,70-y+10).move(x,y).fill('#7A3E2A').stroke(o(1.6));g.rect(22,6).move(x-2,y).fill(INK)});
  for(let r=0;r<2;r++)for(let c=0;c<6;c++)g.rect(18,14).move(36+c*34,100+r*30).fill('#F2D58A').stroke(o(1.1));
  shade(g,g.rect(220,30).move(20,140));g.circle(30).center(49,-4).fill('#555').opacity(.35);g.circle(22).center(92,10).fill('#555').opacity(.3)}];
I.warehouse=[240,120,(g,acc)=>{poly(g,[[10,50],[120,10],[230,50],[230,118],[10,118]],'#C9C3B4',2);for(let x=20;x<230;x+=12)g.line(x,50,x,118).stroke({color:'#00000025',width:2});
  g.rect(60,56).move(90,62).fill(NAVY).stroke(o(1.6));for(let y=66;y<118;y+=8)g.line(90,y,150,y).stroke({color:'#FFFFFF30',width:2});shade(g,g.rect(220,24).move(10,94))}];
I.coins=[160,120,(g,acc)=>{[[20,4],[70,8],[110,5]].forEach(([x,n],k)=>{for(let i=0;i<n;i++){g.ellipse(46,14).move(x,104-i*9).fill(i%2?'#C9A24A':'#D9B55A').stroke(o(1.3))}
  g.ellipse(46,14).move(x,104-n*9).fill('#E8C86E').stroke(o(1.3));g.text('₹').font({size:10,weight:'bold',family:'Inter'}).fill('#8A6A22').center(x+23,111-n*9)})}];
I.banknote=[200,96,(g,acc)=>{g.rect(200,96).radius(4).fill('#9CC7A4').stroke(o(1.8));g.rect(184,80).move(8,8).fill('none').stroke({color:'#2E6B47',width:1.4});
  g.circle(46).center(140,48).fill('#7DB389').stroke({color:'#2E6B47',width:1.4});g.text('₹').font({size:34,weight:'bold',family:'Inter'}).fill('#2E6B47').center(50,46);
  for(let k=0;k<4;k++)g.line(20,70+k*4,90,70+k*4).stroke({color:'#2E6B47',width:1});shade(g,g.rect(200,30).move(0,66))}];
I.moneybag=[130,150,(g,acc)=>{g.path('M40 34 Q20 60 14 100 Q10 146 65 146 Q120 146 116 100 Q110 60 90 34 Z').fill('#C9A46A').stroke(o(2));
  g.path('M44 34 L86 34 L96 16 Q65 26 34 16 Z').fill('#B8925A').stroke(o(1.8));g.rect(52,6).move(39,32).fill(INK);
  g.text('₹').font({size:46,weight:'bold',family:'Inter'}).fill('#6B4E14').center(65,96);shade(g,g.path('M90 60 Q112 90 112 110 Q110 140 70 144 Q100 120 90 60 Z'))}];
I.smartphone=[80,150,(g,acc)=>{g.rect(80,150).radius(12).fill(INK);g.rect(70,124).move(5,12).radius(4).fill('#DCE9EF');
  [[10,22,48,10,acc],[22,40,48,10,'#FFFFFF'],[10,58,40,10,acc],[22,76,48,10,'#FFFFFF']].forEach(([x,y,w,h,c])=>g.rect(w,h).move(x,y).radius(5).fill(c).stroke({color:'#00000030',width:1}));
  g.rect(24,4).move(28,5).radius(2).fill('#333')}];
I.laptop=[200,130,(g,acc)=>{g.rect(150,100).move(25,4).radius(6).fill(INK);g.rect(138,88).move(31,10).fill('#DCE9EF');
  for(let k=0;k<5;k++)g.rect(60+(k%2)*30,6).move(44,22+k*14).fill(k===0?acc:'#9AB')
  ;poly(g,[[8,108],[192,108],[200,122],[0,122]],'#B9BEC2',1.8);g.rect(40,4).move(80,110).fill('#8A9095')}];
I.television=[170,150,(g,acc)=>{g.rect(170,120).radius(14).fill('#5A3E2B').stroke(o(2));g.rect(118,96).move(12,12).radius(18).fill('#2B3238');
  g.rect(118,96).move(12,12).radius(18).fill(dots(g)).opacity(.6);[34,60,86].forEach(y=>g.circle(14).center(150,y).fill('#C9B79A').stroke(o(1.2)));
  g.line(40,0,70,-26).stroke(o(2));g.line(100,0,72,-26).stroke(o(2));g.rect(14,24).move(20,120).fill('#3A281C');g.rect(14,24).move(136,120).fill('#3A281C')}];
I.newspaper=[170,200,(g,acc)=>{g.rect(170,200).fill('#F1EDE3').stroke(o(1.8));g.rect(150,18).move(10,10).fill(INK);
  g.rect(150,4).move(10,32).fill(INK);g.rect(70,56).move(10,44).fill('#C9C3B4').stroke(o(1));
  for(let k=0;k<6;k++)g.rect(66,4).move(94,48+k*9).fill('#9A958A');for(let k=0;k<7;k++)g.rect(150,4).move(10,110+k*12).fill('#9A958A')}];
I.documents=[160,190,(g,acc)=>{[[18,12,-6],[8,6,3],[0,0,0]].forEach(([x,y,r],i)=>{const d=g.group();d.rect(140,180).move(x,y).fill(i===2?'#FBFAF6':'#ECE7DB').stroke(o(1.6));
  if(i===2){d.rect(80,8).move(16,18).fill(INK);for(let k=0;k<12;k++)d.rect(k%4===3?70:108,4).move(16,40+k*11).fill('#9A958A');d.rect(60,10).move(16,96).fill(acc).opacity(.7)}
  d.attr({transform:`rotate(${r},${x+70},${y+90})`})})}];
I.skyscraper=[110,260,(g,acc)=>{g.rect(80,240).move(15,20).fill('#5E7380').stroke(o(2));g.rect(40,20).move(35,0).fill('#4C5E69').stroke(o(1.6));
  for(let r=0;r<18;r++)for(let c=0;c<4;c++)g.rect(12,8).move(22+c*18,30+r*12.5).fill((r*4+c)%7===0?'#F2D58A':'#B9D3DE');shade(g,g.rect(30,240).move(65,20))}];
I.building=[260,160,(g,acc)=>{poly(g,[[20,60],[130,14],[240,60]],'#D8D2C2',2);g.rect(240,10).move(10,60).fill('#CFC8B6').stroke(o(1.6));
  for(let k=0;k<8;k++){g.rect(14,74).move(26+k*28,72).fill('#ECE7DB').stroke(o(1.2))}g.rect(240,14).move(10,146).fill('#CFC8B6').stroke(o(1.6));shade(g,g.rect(240,20).move(10,126))}];
I.house=[150,130,(g,acc)=>{poly(g,[[10,56],[75,8],[140,56]],RED,2);g.rect(110,70).move(20,56).fill('#EDE3C9').stroke(o(2));
  g.rect(26,40).move(62,86).fill(NAVY).stroke(o(1.4));g.rect(22,20).move(30,72).fill('#B9D3DE').stroke(o(1.2));g.rect(22,20).move(98,72).fill('#B9D3DE').stroke(o(1.2))}];
I.plane=[300,110,(g,acc)=>{g.path('M20 56 Q20 40 60 40 L250 40 Q290 44 296 56 Q290 68 250 70 L60 70 Q20 70 20 56 Z').fill('#F3F3F0').stroke(o(2));
  poly(g,[[120,56],[190,56],[150,104],[130,104]],'#DADAD4',1.8);poly(g,[[30,46],[60,46],[44,10],[28,10]],acc,1.8);
  for(let k=0;k<12;k++)g.circle(6).center(90+k*13,50).fill('#4C6A7A');g.rect(22,12).move(150,74).radius(6).fill('#BFC3C2').stroke(o(1.2));shade(g,g.rect(230,8).move(50,62))}];
I.train=[300,110,(g,acc)=>{g.path('M10 30 Q10 14 40 14 L250 14 Q296 14 296 60 L296 86 L10 86 Z').fill('#2F5E8C').stroke(o(2));
  g.rect(286,10).move(10,62).fill(acc);for(let k=0;k<7;k++)g.rect(26,20).move(26+k*34,28).fill('#CFE3EA').stroke(o(1.2));
  g.rect(296,6).move(4,92).fill(INK);[40,80,190,230].forEach(x=>{g.circle(18).center(x,96).fill(INK)});shade(g,g.rect(286,14).move(10,72))}];
I.car=[200,90,(g,acc)=>{g.path('M10 60 Q12 42 40 40 L60 18 Q70 10 90 10 L130 10 Q146 10 156 22 L176 40 Q194 44 194 60 L194 70 L10 70 Z').fill(acc).stroke(o(2));
  poly(g,[[66,22],[96,22],[96,40],[54,40]],'#CFE3EA',1.4);poly(g,[[104,22],[134,22],[152,40],[104,40]],'#CFE3EA',1.4);
  [50,154].forEach(x=>{g.circle(30).center(x,72).fill(INK);g.circle(12).center(x,72).fill('#9AA4AA')});shade(g,g.rect(184,12).move(10,56))}];
I.tractor=[220,150,(g,acc)=>{g.rect(100,46).move(60,62).fill(RED).stroke(o(2));poly(g,[[110,62],[110,14],[160,14],[168,62]],'#CFE3EA',1.8);
  g.rect(60,8).move(104,8).fill(RED).stroke(o(1.4));g.rect(8,40).move(76,24).fill(INK);g.rect(30,30).move(160,72).fill(RED).stroke(o(1.6));
  g.circle(86).center(150,104).fill(INK);g.circle(40).center(150,104).fill('#C9A24A').stroke(o(1.2));
  g.circle(48).center(66,124).fill(INK);g.circle(22).center(66,124).fill('#C9A24A').stroke(o(1.2))}];
I['oil barrel']=[90,120,(g,acc)=>{g.rect(80,110).move(5,6).radius(6).fill('#1E3F5A').stroke(o(2));[30,60,90].forEach(y=>g.rect(80,5).move(5,y).fill('#16303F'));
  g.ellipse(80,16).move(5,0).fill('#2B5674').stroke(o(1.6));g.rect(28,28).move(31,50).fill(acc);shade(g,g.rect(26,110).move(59,6))}];
I.globe=[150,170,(g,acc)=>{g.circle(130).center(75,70).fill('#7FB2C9').stroke(o(2));g.path('M40 40 Q60 30 70 50 Q60 70 44 66 Q30 58 40 40 Z M90 80 Q110 70 120 90 Q112 112 92 108 Q80 96 90 80 Z').fill('#D9C38A').stroke(o(1.2));
  g.path('M20 70 Q75 110 130 70').fill('none').stroke({color:'#00000030',width:1.4});g.line(75,136,75,158).stroke(o(4));g.rect(60,8).move(45,158).fill('#6B4E2A').stroke(o(1.4));shade(g,g.circle(130).center(92,78)).opacity(.5)}];
I.person=[60,170,(g,acc)=>{g.circle(30).center(30,18).fill('#2A2A2A');g.path('M10 44 Q30 34 50 44 L54 104 L44 104 L42 168 L32 168 L30 110 L28 168 L18 168 L16 104 L6 104 Z').fill('#2A2A2A')}];
I.crowd=[300,150,(g,acc)=>{for(let k=0;k<11;k++){const x=10+k*26+(k%2)*6,y=26+(k%3)*10,c=k%4===0?acc:['#3A3A3A','#555','#6A6A6A'][k%3];
  g.circle(22).center(x+14,y).fill(c);g.path(`M${x} ${y+16} Q${x+14} ${y+8} ${x+28} ${y+16} L${x+30} 150 L${x-2} 150 Z`).fill(c)}}];
I.megaphone=[170,110,(g,acc)=>{poly(g,[[30,40],[140,6],[140,104],[30,70]],acc,2);g.rect(26,34).move(8,38).fill(INK);g.rect(14,30).move(40,72).fill(INK).attr({transform:'rotate(-15,47,72)'});
  for(let k=0;k<3;k++)g.path(`M${150+k*6} ${34+k*0} q 12 21 0 42`).fill('none').stroke(o(2))}];
I.gavel=[200,150,(g,acc)=>{const m=g.group();m.rect(120,12).move(40,56).radius(5).fill('#A26B36').stroke(o(1.8));
  m.rect(40,64).move(14,30).radius(6).fill('#8B5A2B').stroke(o(2));m.rect(46,8).move(11,38).fill('#6E4520');m.rect(46,8).move(11,78).fill('#6E4520');
  m.attr({transform:'rotate(-28,60,62)'});g.ellipse(110,22).move(46,118).fill('#6E4520').stroke(o(1.8));g.rect(110,10).move(46,129).fill('#5A381A')}];
I['ballot box']=[150,150,(g,acc)=>{g.rect(130,100).move(10,46).fill('#E9E4D8').stroke(o(2));poly(g,[[10,46],[30,20],[160,20],[140,46]],'#D8D2C2',1.8);
  g.rect(50,6).move(62,28).fill(INK);g.rect(34,44).move(66,0).fill('#FFFFFF').stroke(o(1.4)).attr({transform:'rotate(8,83,22)'});g.path('M76 14 l6 8 l12 -14').fill('none').stroke({color:acc,width:3});shade(g,g.rect(130,24).move(10,122))}];
I['light bulb']=[100,150,(g,acc)=>{g.circle(90).center(50,48).fill('#F7D96B').stroke(o(2));g.rect(36,30).move(32,90).fill('#B9BEC2').stroke(o(1.6));
  [98,106,114].forEach(y=>g.line(32,y,68,y).stroke(o(1.2)));g.path('M38 60 Q50 30 62 60').fill('none').stroke({color:'#8A6A22',width:2})}];
I.padlock=[110,140,(g,acc)=>{g.path('M24 60 L24 40 Q24 8 55 8 Q86 8 86 40 L86 60').fill('none').stroke({color:'#7D868C',width:12});
  g.rect(100,80).move(5,58).radius(8).fill(acc).stroke(o(2));g.circle(16).center(55,92).fill(INK);g.rect(6,18).move(52,96).fill(INK)}];
I.book=[160,120,(g,acc)=>{g.rect(140,100).move(10,10).fill(NAVY).stroke(o(2));g.rect(130,92).move(20,14).fill('#F1EDE3');g.rect(14,100).move(10,10).fill('#16203A');
  g.rect(80,10).move(50,40).fill(acc);g.rect(60,4).move(50,60).fill('#9A958A')}];
I.briefcase=[170,130,(g,acc)=>{g.rect(60,24).move(55,6).radius(8).fill('none').stroke({color:INK,width:6});g.rect(160,96).move(5,28).radius(10).fill('#6B4520').stroke(o(2));
  g.rect(160,8).move(5,62).fill('#4E3216');g.rect(22,16).move(74,58).fill('#C9A24A').stroke(o(1.2));shade(g,g.rect(160,30).move(5,94))}];
I.pill=[160,90,(g,acc)=>{g.rect(140,50).move(10,20).radius(25).fill('#FFFFFF').stroke(o(2));g.path('M80 20 L135 20 Q160 20 160 45 Q160 70 135 70 L80 70 Z').fill(acc).stroke(o(2))}];
I.tower=[120,220,(g,acc)=>{poly(g,[[60,0],[20,220],[100,220]],'none',2);for(let k=1;k<8;k++){const y=k*27,hw=k*5.2;g.line(60-hw,y,60+hw,y).stroke(o(1.4));g.line(60-hw,y,60+hw+5,y+27).stroke(o(1))}
  [24,40].forEach((r,i)=>g.path(`M${60-r} ${20-i*4} Q60 ${-10-r*.4} ${60+r} ${20-i*4}`).fill('none').stroke({color:acc,width:3}))}];
I.chart=[200,150,(g,acc)=>{g.rect(200,150).fill('#FBFAF6').stroke(o(1.8));[60,40,90,70,120].forEach((h,i)=>g.rect(24,h).move(20+i*34,136-h).fill(i===4?acc:'#9AA4AA').stroke(o(1.2)));
  g.polyline([[32,96],[66,110],[100,70],[134,84],[168,30]].map(p=>p.join(',')).join(' ')).fill('none').stroke({color:RED,width:3})}];
I.port=[320,170,(g,acc)=>{g.rect(320,40).move(0,130).fill('#7FA6B8');g.rect(320,24).move(0,106).fill('#8D8577').stroke(o(1.6));
  for(let r=0;r<3;r++)for(let c=0;c<6;c++)g.rect(34,16).move(150+c*28-r*6,90-r*16).fill(CBOX[(r+c)%CBOX.length]).stroke(o(1));
  const cr=g.group();I.crane[2](cr,acc);cr.attr({transform:'translate(20,-14) scale(.55)'})}];
I['auto rickshaw']=[200,150,(g,acc)=>{g.path('M40 30 Q60 10 120 12 L170 14 Q186 16 186 40 L186 116 L30 116 L30 60 Z').fill('#F2C200').stroke(o(2));
  g.rect(156,40).move(30,76).fill('#2E7D5B').stroke(o(1.6));g.rect(44,40).move(120,30).fill('#CFE3EA').stroke(o(1.4));g.path('M40 34 Q70 22 110 24 L110 70 L36 70 Z').fill('#1C1C1C').opacity(.85);
  [[52,122],[164,122]].forEach(([x,y])=>{g.circle(34).center(x,y).fill(INK);g.circle(12).center(x,y).fill('#9AA4AA')});g.circle(28).center(28,122).fill(INK)}];
I.scooter=[180,130,(g,acc)=>{g.path('M30 90 Q40 60 80 60 L120 60 Q130 30 150 22 L158 30 Q144 40 140 64 L150 96 L40 100 Z').fill(acc).stroke(o(2));
  g.rect(50,10).move(66,50).radius(5).fill(INK);[[40,104],[150,104]].forEach(([x,y])=>{g.circle(40).center(x,y).fill(INK);g.circle(16).center(x,y).fill('#9AA4AA')});g.line(150,22,170,16).stroke(o(4))}];
I.bus=[300,140,(g,acc)=>{g.rect(280,96).move(10,14).radius(14).fill('#C8402C').stroke(o(2));for(let k=0;k<7;k++)g.rect(30,30).move(26+k*36,28).fill('#CFE3EA').stroke(o(1.2));
  g.rect(280,10).move(10,70).fill('#F2C200');[[60,114],[240,114]].forEach(([x,y])=>{g.circle(34).center(x,y).fill(INK);g.circle(12).center(x,y).fill('#9AA4AA')})}];
I.arch=[220,220,(g,acc)=>{g.rect(180,190).move(20,20).fill('#C9A27A').stroke(o(2));g.path('M70 210 L70 110 Q110 60 150 110 L150 210 Z').fill('#EFE8DA').stroke(o(1.8));
  g.rect(200,22).move(10,0).fill('#B88E66').stroke(o(1.8));for(let y=40;y<200;y+=24)g.line(20,y,200,y).stroke({color:'#00000020',width:2});g.rect(40,8).move(90,36).fill(INK).opacity(.6)}];
I['round parliament']=[300,140,(g,acc)=>{g.ellipse(280,60).move(10,60).fill('#D8C7A6').stroke(o(2));g.rect(280,40).move(10,90).fill('#D8C7A6').stroke(o(1.6));
  for(let k=0;k<20;k++)g.rect(6,34).move(20+k*14,94).fill('#B7A27C');g.ellipse(280,30).move(10,52).fill('#E9DCC0').stroke(o(1.6));g.ellipse(80,30).move(110,30).fill('#C9B48C').stroke(o(1.4))}];
I.temple=[200,230,(g,acc)=>{g.path('M100 0 L140 90 L60 90 Z').fill('#D86A2A').stroke(o(2));g.rect(4,18).move(98,-14).fill(INK);g.polygon('104,-14 120,-8 104,-2').fill('#E0442C');
  g.rect(120,40).move(40,90).fill('#E9B97A').stroke(o(1.8));g.rect(180,90).move(10,130).fill('#F2D2A0').stroke(o(2));g.path('M80 220 L80 170 Q100 150 120 170 L120 220 Z').fill('#6B4520').stroke(o(1.6))}];
I.hut=[200,150,(g,acc)=>{g.path('M0 70 L100 6 L200 70 Z').fill('#C9A24A').stroke(o(2));for(let k=0;k<12;k++)g.line(10+k*16,64,100,10).stroke({color:'#8A6A22',width:1.2});
  g.rect(160,76).move(20,70).fill('#D9B98A').stroke(o(2));g.rect(36,50).move(82,96).fill('#6B4520').stroke(o(1.6))}];
I.chai=[120,120,(g,acc)=>{g.path('M20 30 L100 30 L90 110 L30 110 Z').fill('#F4F2EC').stroke(o(2));g.ellipse(80,14).move(20,24).fill('#B5733A').stroke(o(1.6));
  for(let k=0;k<3;k++)g.path(`M${44+k*14} 18 q -6 -8 0 -14 t 0 -14`).fill('none').stroke({color:'#9A958A',width:2})}];
I['cricket bat']=[90,240,(g,acc)=>{g.rect(16,70).move(37,0).radius(6).fill(INK);g.path('M24 70 L66 70 L70 220 Q45 236 20 220 Z').fill('#E8C98E').stroke(o(2));
  g.circle(34).center(70,206).fill('#C8402C').stroke(o(1.6));g.path('M58 196 q 12 10 24 0').fill('none').stroke({color:'#FFFFFF',width:2})}];
I.scales=[200,200,(g,acc)=>{g.rect(8,150).move(96,30).fill('#B8925A').stroke(o(1.4));g.rect(80,12).move(60,180).fill('#8A6A22').stroke(o(1.6));g.line(20,40,180,40).stroke(o(4));
  [[40,40],[160,40]].forEach(([x,y])=>{g.line(x,y,x-22,y+70).stroke(o(1.4));g.line(x,y,x+22,y+70).stroke(o(1.4));g.path(`M${x-30} ${y+70} Q${x} ${y+100} ${x+30} ${y+70} Z`).fill('#D9B55A').stroke(o(1.6))});g.circle(14).center(100,30).fill('#D9B55A').stroke(o(1.4))}];
I.handcuffs=[200,120,(g,acc)=>{[[50,64],[150,64]].forEach(([x,y])=>{g.circle(80).center(x,y).fill('none').stroke({color:'#7D868C',width:12});g.circle(80).center(x,y).fill('none').stroke(o(1.4))});
  for(let k=0;k<3;k++)g.ellipse(16,10).move(84+k*12,58).fill('none').stroke({color:'#7D868C',width:4})}];
I.microphone=[90,220,(g,acc)=>{g.rect(60,90).move(15,0).radius(30).fill('#3A3A3A').stroke(o(2));for(let y=14;y<80;y+=10)g.line(20,y,70,y).stroke({color:'#666',width:2});
  g.path('M5 70 Q5 130 45 130 Q85 130 85 70').fill('none').stroke(o(3));g.rect(8,60).move(41,130).fill(INK);g.rect(60,10).move(15,190).radius(4).fill(INK)}];
I.camera=[200,140,(g,acc)=>{g.rect(180,110).move(10,26).radius(12).fill('#2B2B2B').stroke(o(2));g.rect(50,20).move(30,10).radius(4).fill('#2B2B2B');
  g.circle(80).center(100,80).fill('#5B6770').stroke({color:'#111',width:6});g.circle(40).center(100,80).fill('#1E2B4A');g.circle(10).center(90,70).fill('#FFFFFF').opacity(.6);g.rect(24,10).move(150,40).fill(acc)}];
I.rocket=[120,240,(g,acc)=>{g.path('M60 0 Q100 40 96 170 L24 170 Q20 40 60 0 Z').fill('#F4F2EC').stroke(o(2));g.circle(30).center(60,70).fill('#5BA8D9').stroke(o(1.6));
  g.polygon('24,130 0,190 24,180').fill(acc).stroke(o(1.4));g.polygon('96,130 120,190 96,180').fill(acc).stroke(o(1.4));g.path('M40 172 Q60 240 80 172 Z').fill('#F07A1A');g.path('M50 172 Q60 210 70 172 Z').fill('#F2C200')}];
I.satellite=[260,140,(g,acc)=>{[[0,40],[180,40]].forEach(([x,y])=>{g.rect(80,60).move(x,y).fill('#1E3F7A').stroke(o(1.6));for(let k=1;k<4;k++)g.line(x+k*20,y,x+k*20,y+60).stroke({color:'#7FA6D8',width:1.2})});
  g.line(80,70,100,70).stroke(o(3));g.line(160,70,180,70).stroke(o(3));g.rect(60,70).move(100,35).fill('#D9B55A').stroke(o(2));g.path('M130 35 L120 10 L140 10 Z').fill('#B9BEC2').stroke(o(1.4))}];
I['solar panel']=[220,150,(g,acc)=>{g.polygon('20,40 200,40 220,110 0,110').fill('#1E3F7A').stroke(o(2));for(let k=1;k<6;k++)g.line(20+k*30,40,k*36.6,110).stroke({color:'#7FA6D8',width:1.4});
  g.line(10,75,210,75).stroke({color:'#7FA6D8',width:1.4});g.rect(10,40).move(105,110).fill('#7D868C')}];
I['wind turbine']=[160,260,(g,acc)=>{g.polygon('74,60 86,60 92,260 68,260').fill('#F4F2EC').stroke(o(1.6));g.circle(16).center(80,56).fill('#DDD').stroke(o(1.4));
  [0,120,240].forEach(a=>g.path('M80 56 L76 -10 Q80 -20 86 -10 Z').fill('#F4F2EC').stroke(o(1.4)).attr({transform:`rotate(${a},80,56)`}))}];
I.hospital=[240,170,(g,acc)=>{g.rect(220,130).move(10,36).fill('#F4F2EC').stroke(o(2));g.rect(70,160).move(85,6).fill('#E9E4D8').stroke(o(2));
  g.rect(16,50).move(112,20).fill('#C8402C');g.rect(50,16).move(95,37).fill('#C8402C');for(let k=0;k<3;k++){g.rect(26,20).move(24,60+k*32).fill('#B9D3DE');g.rect(26,20).move(190,60+k*32).fill('#B9D3DE')}
  g.rect(40,40).move(100,126).fill('#1E5C78')}];
I.school=[240,170,(g,acc)=>{g.rect(220,110).move(10,56).fill('#D88A4A').stroke(o(2));poly(g,[[0,60],[120,10],[240,60]],'#B65A3A',2);
  g.circle(30).center(120,46).fill('#F4F2EC').stroke(o(1.4));for(let k=0;k<4;k++)g.rect(30,26).move(22+k*54,78).fill('#B9D3DE').stroke(o(1.2));g.rect(36,46).move(102,120).fill('#6B4520')}];
I.bridge=[300,130,(g,acc)=>{g.rect(300,40).move(0,90).fill('#7FA6B8');g.rect(300,12).move(0,60).fill('#8D8577').stroke(o(1.6));
  [60,240].forEach(x=>{g.rect(14,90).move(x-7,0).fill('#C8402C').stroke(o(1.4))});g.path('M0 60 Q60 -10 150 50 Q240 -10 300 60').fill('none').stroke({color:'#C8402C',width:4});
  for(let x=20;x<300;x+=20)g.line(x,60,x,40+Math.abs(150-x)*.18).stroke({color:'#C8402C',width:1.2})}];
I.dam=[300,160,(g,acc)=>{g.rect(300,60).move(0,0).fill('#7FA6B8');poly(g,[[20,40],[280,40],[300,160],[0,160]],'#B9B5AC',2);
  for(let k=0;k<5;k++)g.rect(20,50).move(50+k*44,60).fill('#5B88A0').opacity(.8);g.rect(300,8).move(0,32).fill('#8D8577').stroke(o(1.4))}];
I.hourglass=[110,180,(g,acc)=>{g.rect(110,14).fill('#6B4520').stroke(o(1.6));g.rect(110,14).move(0,166).fill('#6B4520').stroke(o(1.6));
  g.path('M14 14 Q14 70 55 90 Q96 70 96 14 Z').fill('#F4F2EC').stroke(o(1.6));g.path('M14 166 Q14 110 55 90 Q96 110 96 166 Z').fill('#F4F2EC').stroke(o(1.6));
  g.path('M30 40 Q55 70 80 40 Z').fill('#D9B55A');g.path('M24 166 Q55 120 86 166 Z').fill('#D9B55A');g.line(55,90,55,140).stroke({color:'#D9B55A',width:2})}];
I.key=[200,90,(g,acc)=>{g.circle(70).center(40,45).fill('#D9B55A').stroke(o(2));g.circle(26).center(40,45).fill('#EFE8DA').stroke(o(1.4));
  g.rect(120,14).move(70,38).fill('#D9B55A').stroke(o(1.6));g.rect(12,24).move(160,50).fill('#D9B55A').stroke(o(1.4));g.rect(12,18).move(178,50).fill('#D9B55A').stroke(o(1.4))}];
I.calendar=[160,170,(g,acc)=>{g.rect(160,150).move(0,20).radius(8).fill('#FBFAF6').stroke(o(2));g.rect(160,40).move(0,20).radius(8).fill('#C8402C').stroke(o(2));
  [30,130].forEach(x=>g.rect(10,30).move(x-5,6).radius(4).fill(INK));for(let r=0;r<4;r++)for(let c=0;c<6;c++)g.rect(16,14).move(12+c*24,72+r*22).fill(r===1&&c===3?acc:'#D8D2C2')}];
I.man=[70,190,(g,acc)=>{g.circle(34).center(35,20).fill('#C68E64');g.path('M18 12 Q35 -4 52 12 L52 16 Q35 8 18 16 Z').fill('#2A2A2A');
  g.path('M10 46 Q35 36 60 46 L64 118 L6 118 Z').fill('#1E5C78');g.rect(20,70).move(12,118).fill('#2A2A2A');g.rect(20,70).move(38,118).fill('#2A2A2A')}];
I.woman=[70,190,(g,acc)=>{g.path('M14 26 Q14 0 35 0 Q56 0 56 26 L58 58 L12 58 Z').fill('#2A2A2A');g.circle(30).center(35,22).fill('#C68E64');
  g.path('M12 50 Q35 40 58 50 L70 186 L0 186 Z').fill('#C8402C');g.path('M12 50 Q50 80 70 186 L58 186 Q40 100 12 60 Z').fill('#E0A030').opacity(.9)}];
// ---- period versions: the director picks these when the story is set before the modern object existed ----
I.steamer=[300,170,(g,acc)=>{ // ocean liner / steamship, about 1900-1930: black hull, red boot line, tall funnels, smoke
  g.path('M6 104 L294 104 L276 150 L30 150 Z').fill('#1C1C1C').stroke(o(2));g.rect(262,9).move(22,138).fill(RED);
  for(let k=0;k<16;k++)g.circle(5).center(36+k*15,118).fill('#E8DFC6');
  g.rect(230,22).move(36,82).fill('#F1ECDE').stroke(o(1.6));g.rect(170,16).move(66,66).fill('#F1ECDE').stroke(o(1.4));
  for(let k=0;k<14;k++)g.rect(8,8).move(44+k*15,89).fill('#4C6A7A');
  [[96,'#E0A030'],[140,'#E0A030'],[184,'#E0A030']].forEach(([x,c])=>{g.rect(20,48).move(x,18).fill(c).stroke(o(1.6));g.rect(20,9).move(x,18).fill(INK)});
  [[106,12],[150,6],[194,10]].forEach(([x,y],i)=>{g.circle(22-i*2).center(x-10-i*6,y).fill('#8A8A84').opacity(.55);g.circle(16).center(x-26-i*8,y-8).fill('#8A8A84').opacity(.35)});
  g.line(40,104,40,30).stroke(o(2));g.line(262,104,262,34).stroke(o(2));g.line(40,30,262,34).stroke(o(1));shade(g,g.rect(250,8).move(32,96))}];
I.steamtrain=[300,130,(g,acc)=>{ // steam locomotive: boiler, chimney, cab, big driving wheels
  g.rect(150,46).move(70,40).radius(20).fill('#2A2A2A').stroke(o(2));g.rect(16,12).move(204,46).fill('#B08A3A');
  g.rect(18,30).move(190,12).fill(INK).stroke(o(1.6));g.rect(26,8).move(186,8).fill(INK);
  g.circle(26).center(176,10).fill('#B9B5AC').opacity(.6);g.circle(34).center(150,0).fill('#B9B5AC').opacity(.4);
  g.rect(70,74).move(10,12).fill(RED).stroke(o(2));g.rect(26,24).move(28,24).fill('#E8DFC6').stroke(o(1.2));g.rect(84,8).move(4,8).fill(INK);
  g.rect(240,10).move(10,86).fill(INK);poly(g,[[236,86],[270,86],[290,112],[226,112]],'#3A3A3A',1.6);
  [[60,104,34],[120,104,34],[172,108,26]].forEach(([x,y,r])=>{g.circle(r).center(x,y).fill(INK);g.circle(r*.6).center(x,y).fill(RED).stroke(o(1))});
  g.line(60,104,172,108).stroke({color:'#B9B5AC',width:3});shade(g,g.rect(150,10).move(70,74))}];
I.biplane=[300,130,(g,acc)=>{ // early aircraft: two wings, struts, a wooden propeller
  g.rect(240,12).move(30,20).radius(6).fill('#D9C9A3').stroke(o(1.8));g.rect(220,12).move(40,78).radius(6).fill('#D9C9A3').stroke(o(1.8));
  [[70,32,78],[110,32,78],[190,32,78],[230,32,78]].forEach(([x,a,b])=>g.line(x,a,x,b).stroke(o(1.6)));
  g.path('M60 66 Q60 54 90 54 L250 58 Q276 62 276 70 Q276 78 250 80 L90 82 Q60 82 60 66 Z').fill(RED).stroke(o(2));
  poly(g,[[60,60],[30,40],[22,40],[30,72],[64,74]],RED,1.6);g.circle(14).center(276,70).fill(INK);
  g.rect(6,50).move(279,45).radius(3).fill('#8A5A2B').stroke(o(1.2));g.circle(20).center(160,62).fill('#3A3A3A');
  [[130,98],[200,98]].forEach(([x,y])=>{g.line(x,82,x,y).stroke(o(1.6));g.circle(18).center(x,y+6).fill(INK)});shade(g,g.rect(200,6).move(70,74))}];
I.rotaryphone=[180,140,(g,acc)=>{ // the desk telephone before mobiles
  g.path('M20 130 Q16 70 60 62 L120 62 Q164 70 160 130 Z').fill('#1C1C1C').stroke(o(2));
  g.circle(62).center(90,100).fill('#E8DFC6').stroke(o(1.6));for(let k=0;k<10;k++){const a=-2.4+k*.5;g.circle(9).center(90+Math.cos(a)*21,100+Math.sin(a)*21).fill('#1C1C1C')}
  g.circle(18).center(90,100).fill(RED).stroke(o(1));
  g.path('M14 44 Q10 22 34 18 L146 18 Q170 22 166 44 L150 50 Q148 34 134 34 L46 34 Q32 34 30 50 Z').fill('#2A2A2A').stroke(o(2));shade(g,g.rect(130,8).move(25,118))}];
I.oldcar=[220,120,(g,acc)=>{ // an early motor car, boxy with spoked wheels
  g.rect(110,40).move(70,22).fill('#1C1C1C').stroke(o(2));g.rect(36,26).move(110,30).fill('#CFE3EA').stroke(o(1.2));
  g.rect(186,26).move(14,60).radius(4).fill(NAVY).stroke(o(2));g.rect(50,26).move(14,44).fill(NAVY).stroke(o(1.8));g.rect(10,30).move(8,44).fill('#B08A3A');
  [52,170].forEach(x=>{g.circle(44).center(x,94).fill(INK);g.circle(30).center(x,94).fill('#E8DFC6');for(let k=0;k<8;k++){const a=k*Math.PI/4;g.line(x,94,x+Math.cos(a)*14,94+Math.sin(a)*14).stroke(o(1.4))}});
  g.path('M24 66 Q52 50 80 66').fill('none').stroke(o(2));g.path('M142 66 Q170 50 198 66').fill('none').stroke(o(2));shade(g,g.rect(180,6).move(18,80))}];
window.ILLU=I;
})();
