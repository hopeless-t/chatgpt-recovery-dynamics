#!/usr/bin/env python3
"""Generate the deterministic Purrtocol Second Light experimental GLB.

No third-party packages are required. The asset deliberately remains separate
from the canonical First Light artifact.
"""
from __future__ import annotations
import argparse, json, math, struct
from pathlib import Path

MATERIALS = [
    ("cyan", [0.16, 0.78, 0.72, 1.0], 0.48, 0.08),
    ("deep", [0.035, 0.09, 0.14, 1.0], 0.58, 0.04),
    ("amber", [0.95, 0.60, 0.14, 1.0], 0.38, 0.10),
    ("red", [0.88, 0.18, 0.22, 1.0], 0.46, 0.05),
    ("green", [0.16, 0.76, 0.35, 1.0], 0.42, 0.05),
    ("white", [0.94, 0.97, 1.0, 1.0], 0.52, 0.02),
]
REQUIRED_NODES = [
    "root","head","ear_L","ear_R","eye_L","eye_R","eyelid_L","eyelid_R",
    "mouth","paw_FL","paw_FR","paw_BL","paw_BR","tail","goggles",
    "socket_packet","socket_snapshot",
]
ANIMATIONS = [
    "idle_observe","blocked_429","provisional_step_E",
    "stable_snapshot_carry_H","duplicate_retry_attempt",
    "director_neck_scruff_stop",
]

def pad4(data: bytes, fill: bytes=b"\x00") -> bytes:
    return data + fill * ((-len(data)) % 4)

def uv_sphere(lat=8, lon=12):
    pos=[]; nrm=[]; idx=[]
    pos.append((0.0,1.0,0.0)); nrm.append((0.0,1.0,0.0))
    for i in range(1,lat):
        phi=math.pi*i/lat
        y=math.cos(phi); r=math.sin(phi)
        for j in range(lon):
            th=2*math.pi*j/lon
            x=r*math.cos(th); z=r*math.sin(th)
            pos.append((x,y,z)); nrm.append((x,y,z))
    south=len(pos); pos.append((0.0,-1.0,0.0)); nrm.append((0.0,-1.0,0.0))
    def ring(i,j): return 1+(i-1)*lon+(j%lon)
    for j in range(lon):
        idx += [0, ring(1,j+1), ring(1,j)]
    for i in range(1,lat-1):
        for j in range(lon):
            a=ring(i,j); b=ring(i,j+1); c=ring(i+1,j); d=ring(i+1,j+1)
            idx += [a,b,c, b,d,c]
    for j in range(lon):
        idx += [ring(lat-1,j), ring(lat-1,j+1), south]
    return pos,nrm,idx

def quat(axis, deg):
    x,y,z=axis; s=math.sin(math.radians(deg)/2); c=math.cos(math.radians(deg)/2)
    return [x*s,y*s,z*s,c]

class Bin:
    def __init__(self):
        self.data=bytearray(); self.views=[]; self.accessors=[]
    def align(self):
        while len(self.data)%4: self.data.append(0)
    def add(self, payload: bytes, target=None):
        self.align(); off=len(self.data); self.data.extend(payload)
        v={"buffer":0,"byteOffset":off,"byteLength":len(payload)}
        if target: v["target"]=target
        self.views.append(v); return len(self.views)-1
    def f32(self, vals, typ, count, *, minv=None, maxv=None, target=None):
        flat=[]
        for v in vals:
            if isinstance(v,(list,tuple)): flat.extend(v)
            else: flat.append(v)
        view=self.add(struct.pack("<"+"f"*len(flat), *flat), target)
        a={"bufferView":view,"componentType":5126,"count":count,"type":typ}
        if minv is not None: a["min"]=minv
        if maxv is not None: a["max"]=maxv
        self.accessors.append(a); return len(self.accessors)-1
    def u16(self, vals):
        view=self.add(struct.pack("<"+"H"*len(vals), *vals), 34963)
        a={"bufferView":view,"componentType":5123,"count":len(vals),"type":"SCALAR"}
        self.accessors.append(a); return len(self.accessors)-1

def node(name, mesh=None, t=(0,0,0), s=(1,1,1), r=None, children=None):
    d={"name":name}
    if mesh is not None: d["mesh"]=mesh
    if t!=(0,0,0): d["translation"]=list(t)
    if s!=(1,1,1): d["scale"]=list(s)
    if r is not None: d["rotation"]=r
    if children: d["children"]=children
    return d

def build():
    pos,nrm,idx=uv_sphere()
    b=Bin()
    pos_acc=b.f32(pos,"VEC3",len(pos),
                  minv=[min(p[k] for p in pos) for k in range(3)],
                  maxv=[max(p[k] for p in pos) for k in range(3)], target=34962)
    nrm_acc=b.f32(nrm,"VEC3",len(nrm), target=34962)
    idx_acc=b.u16(idx)
    mats=[]; meshes=[]
    for name,color,rough,metal in MATERIALS:
        mats.append({"name":name,"pbrMetallicRoughness":{
            "baseColorFactor":color,"roughnessFactor":rough,"metallicFactor":metal}})
        meshes.append({"name":"organic_"+name,"primitives":[{
            "attributes":{"POSITION":pos_acc,"NORMAL":nrm_acc},
            "indices":idx_acc,"material":len(mats)-1
        }]})
    C,D,A,R,G,W=range(6)

    nodes=[]
    def add(*args,**kwargs):
        nodes.append(node(*args,**kwargs)); return len(nodes)-1
    root=add("root")
    add("body",C,t=(0,0.82,0),s=(0.72,0.92,0.58))
    add("head",C,t=(0,1.72,0.06),s=(0.63,0.57,0.56))
    add("ear_L",C,t=(-0.38,2.20,0.02),s=(0.20,0.34,0.16),r=quat((0,0,1),18))
    add("ear_R",C,t=(0.38,2.20,0.02),s=(0.20,0.34,0.16),r=quat((0,0,1),-18))
    add("eye_L",W,t=(-0.22,1.80,0.52),s=(0.11,0.15,0.07))
    add("eye_R",W,t=(0.22,1.80,0.52),s=(0.11,0.15,0.07))
    add("eyelid_L",D,t=(-0.22,1.83,0.585),s=(0.12,0.045,0.025))
    add("eyelid_R",D,t=(0.22,1.83,0.585),s=(0.12,0.045,0.025))
    add("mouth",D,t=(0,1.52,0.57),s=(0.13,0.045,0.03))
    add("paw_FL",C,t=(-0.42,0.30,0.31),s=(0.23,0.38,0.25))
    add("paw_FR",C,t=(0.42,0.30,0.31),s=(0.23,0.38,0.25))
    add("paw_BL",C,t=(-0.38,0.18,-0.24),s=(0.25,0.34,0.28))
    add("paw_BR",C,t=(0.38,0.18,-0.24),s=(0.25,0.34,0.28))
    add("tail",G,t=(0.68,0.93,-0.22),s=(0.15,0.55,0.15),r=quat((0,0,1),-38))
    add("goggles",A,t=(0,1.86,0.61),s=(0.49,0.11,0.07))
    add("socket_packet",t=(-0.66,0.92,0.12))
    add("socket_snapshot",t=(0.68,0.96,0.07))
    add("nose",D,t=(0,1.65,0.62),s=(0.08,0.06,0.05))
    add("brow_L",D,t=(-0.22,1.98,0.55),s=(0.15,0.035,0.025),r=quat((0,0,1),8))
    add("brow_R",D,t=(0.22,1.98,0.55),s=(0.15,0.035,0.025),r=quat((0,0,1),-8))
    add("cheek_L",W,t=(-0.30,1.57,0.43),s=(0.16,0.13,0.10))
    add("cheek_R",W,t=(0.30,1.57,0.43),s=(0.16,0.13,0.10))
    add("packet_prop",C,t=(-0.75,0.93,0.12),s=(0.12,0.12,0.12))
    add("snapshot_prop",A,t=(0.82,0.96,0.08),s=(0.25,0.31,0.12))
    add("lamp_B",R,t=(-0.70,2.55,-0.12),s=(0.10,0.10,0.10))
    add("lamp_E",A,t=(-0.42,2.55,-0.12),s=(0.10,0.10,0.10))
    add("lamp_H",G,t=(-0.14,2.55,-0.12),s=(0.10,0.10,0.10))
    add("whisker_L",W,t=(-0.42,1.55,0.48),s=(0.23,0.025,0.025),r=quat((0,0,1),10))
    add("whisker_R",W,t=(0.42,1.55,0.48),s=(0.23,0.025,0.025),r=quat((0,0,1),-10))
    nodes[root]["children"]=list(range(1,len(nodes)))
    name_to_idx={n["name"]:i for i,n in enumerate(nodes)}

    animations=[]; cubic_count=0; total_channels=0
    def make_anim(name, specs, duration=1.6):
        nonlocal cubic_count,total_channels
        samplers=[]; channels=[]
        times=[0.0,duration*0.5,duration]
        time_acc=b.f32(times,"SCALAR",3,minv=[0.0],maxv=[duration])
        for node_name,path,values,interp in specs:
            typ="VEC4" if path=="rotation" else "VEC3"
            if interp=="CUBICSPLINE":
                expanded=[]; zero=[0.0]*(4 if typ=="VEC4" else 3)
                for v in values: expanded += [zero, v, zero]
                out_acc=b.f32(expanded,typ,9); cubic_count += 1
            else:
                out_acc=b.f32(values,typ,3)
            samplers.append({"input":time_acc,"output":out_acc,"interpolation":interp})
            channels.append({"sampler":len(samplers)-1,"target":{"node":name_to_idx[node_name],"path":path}})
            total_channels += 1
        animations.append({"name":name,"samplers":samplers,"channels":channels})

    make_anim("idle_observe",[
        ("body","translation",[[0,.82,0],[0,.88,0],[0,.82,0]],"CUBICSPLINE"),
        ("head","translation",[[0,1.72,.06],[0,1.76,.07],[0,1.72,.06]],"CUBICSPLINE"),
        ("tail","rotation",[quat((0,0,1),-38),quat((0,0,1),-15),quat((0,0,1),-38)],"LINEAR"),
        ("packet_prop","translation",[[-.75,.93,.12],[-.75,1.02,.12],[-.75,.93,.12]],"CUBICSPLINE"),
        ("ear_L","rotation",[quat((0,0,1),18),quat((0,0,1),24),quat((0,0,1),18)],"LINEAR"),
        ("ear_R","rotation",[quat((0,0,1),-18),quat((0,0,1),-24),quat((0,0,1),-18)],"LINEAR"),
    ])
    make_anim("blocked_429",[
        ("head","translation",[[0,1.72,.06],[0,1.53,.08],[0,1.60,.08]],"CUBICSPLINE"),
        ("ear_L","rotation",[quat((0,0,1),18),quat((0,0,1),62),quat((0,0,1),52)],"LINEAR"),
        ("body","scale",[[.72,.92,.58],[.75,.82,.62],[.74,.86,.60]],"CUBICSPLINE"),
        ("paw_FL","translation",[[-.42,.30,.31],[-.48,.25,.36],[-.44,.28,.33]],"CUBICSPLINE"),
        ("lamp_B","scale",[[.10,.10,.10],[.20,.20,.20],[.12,.12,.12]],"LINEAR"),
    ])
    make_anim("provisional_step_E",[
        ("root","translation",[[0,0,0],[0.16,0,0.03],[0.28,0,0.05]],"CUBICSPLINE"),
        ("paw_FR","translation",[[.42,.30,.31],[.46,.48,.48],[.44,.30,.40]],"CUBICSPLINE"),
        ("head","rotation",[quat((1,0,0),0),quat((1,0,0),-8),quat((1,0,0),0)],"LINEAR"),
        ("goggles","scale",[[.49,.11,.07],[.55,.13,.08],[.49,.11,.07]],"CUBICSPLINE"),
        ("lamp_E","scale",[[.10,.10,.10],[.20,.20,.20],[.12,.12,.12]],"LINEAR"),
    ])
    make_anim("stable_snapshot_carry_H",[
        ("snapshot_prop","translation",[[.82,.96,.08],[.74,1.12,.16],[.82,.96,.08]],"CUBICSPLINE"),
        ("body","translation",[[0,.82,0],[0,.86,0],[0,.82,0]],"CUBICSPLINE"),
        ("tail","rotation",[quat((0,0,1),-38),quat((0,0,1),20),quat((0,0,1),-38)],"LINEAR"),
        ("paw_FR","rotation",[quat((0,0,1),0),quat((0,0,1),-22),quat((0,0,1),0)],"LINEAR"),
        ("lamp_H","scale",[[.10,.10,.10],[.20,.20,.20],[.12,.12,.12]],"CUBICSPLINE"),
    ])
    make_anim("duplicate_retry_attempt",[
        ("packet_prop","translation",[[-.75,.93,.12],[-.28,1.10,.50],[-.75,.93,.12]],"CUBICSPLINE"),
        ("head","rotation",[quat((0,1,0),0),quat((0,1,0),18),quat((0,1,0),0)],"LINEAR"),
        ("paw_FL","rotation",[quat((0,0,1),0),quat((0,0,1),30),quat((0,0,1),0)],"LINEAR"),
        ("paw_FR","rotation",[quat((0,0,1),0),quat((0,0,1),-30),quat((0,0,1),0)],"LINEAR"),
        ("body","scale",[[.72,.92,.58],[.76,.88,.62],[.72,.92,.58]],"CUBICSPLINE"),
    ])
    make_anim("director_neck_scruff_stop",[
        ("root","translation",[[0,0,0],[0,.34,0],[0,.02,0]],"CUBICSPLINE"),
        ("body","rotation",[quat((0,0,1),0),quat((0,0,1),8),quat((0,0,1),-3)],"LINEAR"),
        ("head","rotation",[quat((0,0,1),0),quat((0,0,1),-12),quat((0,0,1),5)],"LINEAR"),
        ("paw_FL","rotation",[quat((1,0,0),0),quat((1,0,0),35),quat((1,0,0),0)],"LINEAR"),
        ("paw_FR","rotation",[quat((1,0,0),0),quat((1,0,0),35),quat((1,0,0),0)],"LINEAR"),
    ], duration=1.8)

    assert len(nodes)==30
    assert total_channels==31
    assert cubic_count==15
    gltf={
        "asset":{"version":"2.0","generator":"Purrtocol Second Light deterministic stdlib generator","extras":{
            "variant_id":"PKV-SECOND-LIGHT-EXPERIMENTAL","classification":"visualization_not_evidence",
            "canonical":False,"human_reaction":"UNKNOWN","technical_quality_not_equal_humor":True}},
        "scene":0,"scenes":[{"nodes":[root]}],"nodes":nodes,"meshes":meshes,"materials":mats,
        "animations":animations,"buffers":[{"byteLength":len(b.data)}],"bufferViews":b.views,"accessors":b.accessors,
    }
    j=pad4(json.dumps(gltf,separators=(",",":"),ensure_ascii=False).encode("utf-8"),b" ")
    binary=pad4(bytes(b.data),b"\x00")
    total=12+8+len(j)+8+len(binary)
    out=struct.pack("<4sII",b"glTF",2,total)
    out+=struct.pack("<II",len(j),0x4E4F534A)+j
    out+=struct.pack("<II",len(binary),0x004E4942)+binary
    return out,{"nodes":len(nodes),"animations":len(animations),"animation_channels":total_channels,
                "cubic_spline_channels":cubic_count,"triangles":len(idx)//3,"textures":0}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); ap.add_argument("--receipt")
    ns=ap.parse_args(); data,metrics=build(); path=Path(ns.output)
    path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)
    if ns.receipt:
        import hashlib
        receipt={"schema":"purrtocol-3d-second-light-receipt/v0","status":"experimental_implemented_visualization",
                 "canonical":False,"promotion":"none","evidence_status":"visualization_not_evidence",
                 "human_reaction":"UNKNOWN","asset":path.name,"asset_bytes":len(data),
                 "asset_sha256":hashlib.sha256(data).hexdigest(),**metrics,
                 "invariants":["Simulation != Evidence","Visualization != Evidence","Generated variant != Canon",
                               "UNKNOWN != SUCCESS","Technical quality != humor"]}
        rp=Path(ns.receipt); rp.parent.mkdir(parents=True,exist_ok=True)
        rp.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"bytes":len(data),**metrics},ensure_ascii=False))

if __name__=="__main__": main()
