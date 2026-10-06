#!/usr/bin/env python3
import argparse,hashlib,json,math,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"data/purrtocol_3d_contract.json"

def q(axis,d):
    r=math.radians(d)/2;s,c=math.sin(r),math.cos(r)
    return {"x":(s,0,0,c),"y":(0,s,0,c),"z":(0,0,s,c)}[axis]
def flat(v):return [x for row in v for x in row]
def pad(b):
    while len(b)%4:b.append(0)

class B:
    def __init__(s):s.bin=bytearray();s.v=[];s.a=[];s.m=[];s.n=[];s.mat=[];s.anim=[]
    def acc(s,vals,count,typ,comp=5126,target=None,lo=None,hi=None):
        pad(s.bin);off=len(s.bin);fmt="f" if comp==5126 else "H"
        raw=struct.pack("<"+fmt*len(vals),*vals);s.bin.extend(raw)
        x={"buffer":0,"byteOffset":off,"byteLength":len(raw)}
        if target:x["target"]=target
        s.v.append(x);a={"bufferView":len(s.v)-1,"byteOffset":0,"componentType":comp,"count":count,"type":typ}
        if lo is not None:a["min"]=lo
        if hi is not None:a["max"]=hi
        s.a.append(a);return len(s.a)-1
    def node(s,name,**kw):
        n={"name":name}
        for k,v in kw.items():
            if v is not None:n[k]=list(v) if isinstance(v,tuple) else v
        s.n.append(n);return len(s.n)-1

def sphere(seg=12,st=8):
    p=[];n=[];idx=[]
    for i in range(st+1):
        ph=math.pi*i/st;y=math.cos(ph);r=math.sin(ph)
        for j in range(seg+1):
            th=2*math.pi*j/seg;x,z=r*math.cos(th),r*math.sin(th);p.append((x,y,z));n.append((x,y,z))
    row=seg+1
    for i in range(st):
        for j in range(seg):
            a=i*row+j;b=a+row;c=b+1;d=a+1
            if i:idx+=(a,b,d)
            if i<st-1:idx+=(d,b,c)
    return p,n,idx
def cube():
    F=[((1,0,0),[(1,-1,-1),(1,1,-1),(1,1,1),(1,-1,1)]),((-1,0,0),[(-1,-1,1),(-1,1,1),(-1,1,-1),(-1,-1,-1)]),
       ((0,1,0),[(-1,1,-1),(-1,1,1),(1,1,1),(1,1,-1)]),((0,-1,0),[(-1,-1,1),(-1,-1,-1),(1,-1,-1),(1,-1,1)]),
       ((0,0,1),[(1,-1,1),(1,1,1),(-1,1,1),(-1,-1,1)]),((0,0,-1),[(-1,-1,-1),(-1,1,-1),(1,1,-1),(1,-1,-1)])]
    p=[];n=[];idx=[]
    for normal,v in F:
        a=len(p);p+=v;n += [normal]*4;idx += (a,a+1,a+2,a,a+2,a+3)
    return p,n,idx
def geo(b,g):
    p,n,i=g
    pa=b.acc(flat(p),len(p),"VEC3",target=34962,lo=[min(x[k] for x in p) for k in range(3)],hi=[max(x[k] for x in p) for k in range(3)])
    na=b.acc(flat(n),len(n),"VEC3",target=34962);ia=b.acc(i,len(i),"SCALAR",5123,34963,[min(i)],[max(i)])
    return pa,na,ia,len(i)//3
def tr(b,t,v,kind,cubic):
    ia=b.acc(t,len(t),"SCALAR",lo=[min(t)],hi=[max(t)])
    if cubic:
        out=[];z=[0.0]*len(v[0])
        for x in v:out+=z+list(x)+z
        oa=b.acc(out,len(v)*3,kind);mode="CUBICSPLINE"
    else:oa=b.acc(flat(v),len(v),kind);mode="LINEAR"
    return ia,oa,mode
def anim(b,name,tracks):
    S=[];C=[]
    for node,path,t,v,cub in tracks:
        ia,oa,mode=tr(b,t,v,"VEC4" if path=="rotation" else "VEC3",cub)
        C.append({"sampler":len(S),"target":{"node":node,"path":path}});S.append({"input":ia,"output":oa,"interpolation":mode})
    b.anim.append({"name":name,"samplers":S,"channels":C,"extras":{"classification":"visualization_not_evidence"}})

def build():
    c=json.loads(CONTRACT.read_text());b=B();gs=geo(b,sphere());gc=geo(b,cube())
    colors={"body":[.10,.72,.62,1],"dark":[.025,.055,.075,1],"white":[.96,.98,.96,1],"amber":[.96,.55,.06,1],
            "red":[.88,.08,.08,1],"green":[.10,.88,.30,1],"cyan":[.08,.82,.95,1],"blue":[.08,.28,.76,1]}
    for name,col in colors.items():
        m={"name":name,"pbrMetallicRoughness":{"baseColorFactor":col,"metallicFactor":0,"roughnessFactor":.5}}
        if name in ("amber","green","cyan"):m["emissiveFactor"]={"amber":[.15,.06,0],"green":[0,.08,.015],"cyan":[0,.06,.08]}[name]
        b.mat.append(m)
    mi={};geom={"sphere":gs,"cube":gc}
    def mesh(shape,mat):
        k=(shape,mat)
        if k not in mi:
            p,n,i,_=geom[shape];b.m.append({"name":shape+"_"+mat,"primitives":[{"attributes":{"POSITION":p,"NORMAL":n},"indices":i,"material":list(colors).index(mat)}]});mi[k]=len(b.m)-1
        return mi[k]
    N={}
    def nd(name,shape=None,mat=None,t=None,r=None,s=None,children=None,extras=None):
        N[name]=b.node(name,mesh=mesh(shape,mat) if shape else None,translation=t,rotation=r,scale=s,children=children,extras=extras);return N[name]
    root=nd("root",t=(0,0,0),extras={"semantic":"runtime_root"})
    nd("body","sphere","body",(0,1.08,0),s=(.76,.86,.62));nd("head","sphere","body",(0,2.05,.10),s=(.70,.64,.64))
    nd("ear_L","sphere","body",(-.38,2.58,.02),q("z",18),(.20,.42,.13));nd("ear_R","sphere","body",(.38,2.58,.02),q("z",-18),(.20,.42,.13))
    nd("eye_L","sphere","white",(-.23,2.12,.60),s=(.16,.19,.08));nd("eye_R","sphere","white",(.23,2.12,.60),s=(.16,.19,.08))
    nd("pupil_L","sphere","dark",(-.23,2.10,.675),s=(.055,.08,.035));nd("pupil_R","sphere","dark",(.23,2.10,.675),s=(.055,.08,.035))
    nd("eyelid_L","sphere","body",(-.23,2.23,.635),s=(.17,.035,.04));nd("eyelid_R","sphere","body",(.23,2.23,.635),s=(.17,.035,.04))
    nd("mouth","sphere","dark",(0,1.88,.742),s=(.11,.025,.018))
    for name,t,s in [("paw_FL",(-.42,.36,.32),(.24,.34,.25)),("paw_FR",(.42,.36,.32),(.24,.34,.25)),("paw_BL",(-.46,.34,-.28),(.27,.36,.30)),("paw_BR",(.46,.34,-.28),(.27,.36,.30))]:nd(name,"sphere","body",t,s=s)
    nd("tail","sphere","body",(.67,1.12,-.37),q("z",-48),(.15,.68,.15));nd("tail_tip","sphere","green",(1.09,1.66,-.37),q("z",-48),(.17,.25,.17))
    gl=nd("goggle_L","sphere","amber",(-.23,2.13,.69),s=(.22,.22,.035));gr=nd("goggle_R","sphere","amber",(.23,2.13,.69),s=(.22,.22,.035))
    nd("goggles",children=[gl,gr]);nd("socket_packet",t=(-.78,1.22,.22));nd("packet_prop","cube","cyan",(-.78,1.22,.22),s=(.14,.09,.06),extras={"semantic":"cheap_observation"})
    nd("socket_snapshot",t=(.82,1.06,.16));nd("snapshot_prop","cube","blue",(.82,1.06,.16),s=(.29,.23,.12),extras={"semantic":"heavy_materialization"})
    nd("state_B","sphere","red",(-.68,2.82,-.05),s=(.08,.08,.08));nd("state_E","sphere","amber",(0,2.88,-.05),s=(.08,.08,.08));nd("state_H","sphere","green",(.68,2.82,-.05),s=(.08,.08,.08))
    b.n[root]["children"]=list(range(1,len(b.n)))
    if set(c["required_nodes"])-set(N):raise SystemExit("missing semantic node")
    T=[0,.75,1.5,2.25,3]
    anim(b,"idle_observe",[(root,"translation",T,[(0,0,0),(0,.055,0),(0,0,0),(0,-.035,0),(0,0,0)],1),(N["head"],"rotation",T,[q("y",x) for x in (-5,7,-2,5,-5)],0),(N["tail"],"rotation",T,[q("z",x) for x in (-52,-34,-48,-68,-52)],0),(N["ear_L"],"rotation",T,[q("z",x) for x in (18,25,13,22,18)],0),(N["packet_prop"],"translation",T,[(-.78,1.22,.22),(-.78,1.28,.22),(-.78,1.22,.22),(-.78,1.26,.22),(-.78,1.22,.22)],1)])
    T=[0,.35,.8,1.35,1.8]
    anim(b,"blocked_429",[(root,"translation",T,[(0,0,0),(0,-.12,0),(0,-.19,0),(0,-.16,0),(0,-.12,0)],1),(N["head"],"rotation",T,[q("x",x) for x in (0,8,15,11,8)],0),(N["ear_L"],"rotation",T,[q("z",x) for x in (18,52,68,62,52)],0),(N["tail"],"rotation",T,[q("z",x) for x in (-48,-78,-92,-86,-78)],0)])
    T=[0,.45,.95,1.5,2.1]
    anim(b,"provisional_step_E",[(root,"translation",T,[(0,0,0),(0,.02,.06),(0,.03,.13),(0,.02,.19),(0,0,.23)],1),(N["paw_FL"],"translation",T,[(-.42,.36,.32),(-.42,.51,.44),(-.42,.39,.52),(-.42,.36,.42),(-.42,.36,.32)],1),(N["paw_FR"],"translation",T,[(.42,.36,.32),(.42,.36,.32),(.42,.42,.35),(.42,.49,.46),(.42,.36,.52)],1),(N["goggles"],"scale",T,[(1,)*3,(1.05,)*3,(1,)*3,(1.04,)*3,(1,)*3],1)])
    T=[0,.6,1.2,1.8,2.4]
    anim(b,"stable_snapshot_carry_H",[(root,"translation",T,[(0,0,0),(0,.04,0),(0,.02,0),(0,.04,0),(0,0,0)],1),(N["snapshot_prop"],"translation",T,[(.82,1.06,.16),(.74,1.25,.30),(.70,1.34,.36),(.74,1.25,.30),(.82,1.06,.16)],1),(N["tail"],"rotation",T,[q("z",x) for x in (-48,-29,-18,-31,-48)],0)])
    T=[0,.22,.44,.72,.94,1.2]
    anim(b,"duplicate_retry_attempt",[(root,"translation",T,[(0,0,0),(0,.02,.13),(0,0,0),(0,.02,.15),(0,0,0),(0,-.03,0)],1),(N["paw_FR"],"translation",T,[(.42,.36,.32),(.42,.58,.48),(.42,.36,.32),(.42,.61,.51),(.42,.36,.32),(.42,.36,.32)],1),(N["head"],"rotation",T,[q("x",x) for x in (0,-8,3,-10,5,0)],0),(N["tail"],"rotation",T,[q("z",x) for x in (-48,-25,-68,-20,-72,-48)],0)])
    T=[0,.35,.8,1.3,1.9,2.6]
    anim(b,"director_neck_scruff_stop",[(root,"translation",T,[(0,0,0),(0,.18,0),(0,.62,0),(0,.82,0),(0,.74,0),(0,.62,0)],1),(N["body"],"rotation",T,[q("z",x) for x in (0,-3,4,-5,3,0)],0),(N["paw_FL"],"rotation",T,[q("z",x) for x in (0,12,28,34,20,10)],0),(N["paw_FR"],"rotation",T,[q("z",x) for x in (0,-12,-28,-34,-20,-10)],0),(N["tail"],"rotation",T,[q("z",x) for x in (-48,-70,-96,-102,-92,-82)],0)])
    if [a["name"] for a in b.anim]!=c["required_animations"]:raise SystemExit("animation contract mismatch")
    G={"asset":{"version":"2.0","generator":"Purrtocol Second Light forge","extras":{"variant_id":"PKV-SECOND-LIGHT-CANDIDATE","classification":"visualization_not_evidence","canonical":False,"promotion":"none","production_intent":"play-straight"}},"scene":0,"scenes":[{"nodes":[root]}],"nodes":b.n,"meshes":b.m,"materials":b.mat,"animations":b.anim,"bufferViews":b.v,"accessors":b.a,"buffers":[{"byteLength":len(b.bin)}]}
    metrics={"scene_nodes":len(b.n),"animation_clips":len(b.anim),"animation_channels":sum(len(a["channels"]) for a in b.anim),"cubic_spline_samplers":sum(s["interpolation"]=="CUBICSPLINE" for a in b.anim for s in a["samplers"]),"linear_samplers":sum(s["interpolation"]=="LINEAR" for a in b.anim for s in a["samplers"]),"materials":len(b.mat),"textures":0,"unique_geometry_triangles":gs[3]+gc[3]}
    metrics["instanced_scene_triangles"]=sum(G["accessors"][p["indices"]]["count"]//3 for n in G["nodes"] if "mesh" in n for p in G["meshes"][n["mesh"]]["primitives"])
    return G,bytes(b.bin),metrics

def encode(g,b):
    j=json.dumps(g,separators=(",",":"),sort_keys=True).encode()
    while len(j)%4:j+=b" "
    b=bytearray(b);pad(b);return struct.pack("<4sII",b"glTF",2,12+8+len(j)+8+len(b))+struct.pack("<II",len(j),0x4E4F534A)+j+struct.pack("<II",len(b),0x004E4942)+b

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",required=True);p.add_argument("--receipt");a=p.parse_args()
    g,b,m=build();data=encode(g,b);out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
    r={"schema":"purrtocol-3d-second-light-candidate/v0","status":"experimental_asset_not_canonical","classification":"implemented_visualization_not_evidence","asset":str(out).replace("\\","/"),"asset_bytes":len(data),"asset_sha256":hashlib.sha256(data).hexdigest(),"metrics":m,"world_laws":{"visualization_is_not_evidence":True,"human_reaction":"UNKNOWN","automatic_promotion":False,"technical_quality_is_not_humor":True},"animation_strategy":{"smooth_translation_scale":"CUBICSPLINE_zero_tangent_ease","rotation":"LINEAR_quaternion_slerp_at_runtime","secondary_motion":["ears","tail","paws","goggles","packet","snapshot"],"viewer_crossfade_candidate_ms":450},"source_contract":"data/purrtocol_3d_contract.json","canonical_asset_unchanged":True}
    if a.receipt:
        rp=Path(a.receipt);rp.parent.mkdir(parents=True,exist_ok=True);rp.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True))
if __name__=="__main__":main()
