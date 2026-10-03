#!/usr/bin/env python3
"""Analyze the intentionally over-engineered Purrtocol expansion event log."""
from __future__ import annotations
import argparse, json, math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z","+00:00"))

def load_events(path):
    out=[json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    out.sort(key=lambda x: parse_ts(x["timestamp_utc"]) if x.get("timestamp_utc") else datetime.max.replace(tzinfo=timezone.utc))
    return out

def linreg(xs,ys):
    xb=sum(xs)/len(xs); yb=sum(ys)/len(ys)
    sxx=sum((x-xb)**2 for x in xs)
    if sxx==0: return 0.0,yb,0.0
    slope=sum((x-xb)*(y-yb) for x,y in zip(xs,ys))/sxx
    intercept=yb-slope*xb
    pred=[intercept+slope*x for x in xs]
    sse=sum((y-p)**2 for y,p in zip(ys,pred)); sst=sum((y-yb)**2 for y in ys)
    return slope,intercept,(1-sse/sst if sst else 1.0)

def logspace(lo,hi,n):
    a,b=math.log(lo),math.log(hi)
    return [math.exp(a+(b-a)*i/(n-1)) for i in range(n)]

def hawkes_loglik(ts,horizon,mu,n_branch,beta):
    alpha=n_branch*beta; total=0.0
    for i,t in enumerate(ts):
        lam=mu+alpha*sum(math.exp(-beta*(t-u)) for u in ts[:i])
        if lam<=0: return float("-inf")
        total+=math.log(lam)
    total-=mu*horizon
    total-=n_branch*sum(1-math.exp(-beta*(horizon-u)) for u in ts)
    return total

def fit_hawkes(ts):
    horizon=max(ts)
    if len(ts)<3 or horizon<=0: return {"fit_status":"insufficient_data"}
    base=len(ts)/horizon; best=(float("-inf"),None)
    for beta in logspace(0.01,100.0,41):
        for j in range(61):
            n_branch=3.0*j/60.0
            for mu in logspace(max(base*0.001,1e-6),max(base*5.0,1e-5),31):
                ll=hawkes_loglik(ts,horizon,mu,n_branch,beta)
                if ll>best[0]: best=(ll,(mu,n_branch,beta))
    ll,(mu,n_branch,beta)=best
    cls="subcritical" if n_branch<0.95 else ("near-critical" if n_branch<=1.05 else "supercritical")
    return {"fit_status":"descriptive_grid_fit","mu_per_hour":mu,"branching_ratio_n":n_branch,"beta_per_hour":beta,"alpha_per_hour":n_branch*beta,"log_likelihood":ll,"classification":cls,"warning":"Selected commit events are sparse, curated, bursty, and right-censored. This fit is not a general law of mascot growth."}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",default="data/pakenya_events.jsonl")
    ap.add_argument("--output")
    ap.add_argument("--quadratic-b",type=float,default=0.02)
    ap.add_argument("--obs-h0",type=float,default=0.0)
    ap.add_argument("--obs-s",type=float,default=0.02)
    args=ap.parse_args()
    events=load_events(Path(args.input))
    timed=[e for e in events if e.get("status")=="implemented" and e.get("timestamp_utc")]
    if len(timed)<2: raise SystemExit("need at least two implemented timestamped events")
    t0=parse_ts(timed[0]["timestamp_utc"])
    ts=[(parse_ts(e["timestamp_utc"])-t0).total_seconds()/3600 for e in timed]
    r,log_p0,r2=linreg(ts,[math.log(i+1) for i in range(len(ts))])
    p0=math.exp(log_p0)
    children=Counter(e.get("parent_event_id") for e in events if e.get("parent_event_id"))
    edges=sum(children.values()); ideas=[e.get("adjacent_ideas_generated",0) for e in events]
    singularity=(1/r)*math.log(1+r/(args.quadratic_b*max(1.0,p0))) if r>0 and args.quadratic_b>0 else None
    expected=p0+r/args.obs_s if r>0 and args.obs_s>0 and args.obs_h0==0 else None
    result={
      "schema":"purrtocol-expansion-analysis/v1",
      "evidence_class":"satirical_side-study_with_commit-backed_event_times",
      "event_log":{"events_total":len(events),"implemented_timestamped_events":len(timed),"roots":sum(1 for e in events if not e.get("parent_event_id")),"edges":edges,"distinct_parents":len(children),"observed_edges_per_event":edges/len(events),"mean_children_among_observed_parents":edges/len(children) if children else 0,"mean_adjacent_ideas_generated_mark":sum(ideas)/len(ideas),"pairwise_contact_surface":len(events)*(len(events)-1)//2,"span_hours":ts[-1]-ts[0]},
      "exponential_growth_fit":{"model":"P(t)=P0*exp(r*t)","r_per_hour":r,"intercept_log_p0":log_p0,"p0_fit":p0,"r2_log_cumulative":r2,"doubling_time_hours":math.log(2)/r if r>0 else None,"warning":"This is a descriptive fit to a manually curated subset of Purrtocol-related commits, not a forecast."},
      "hawkes_fit":fit_hawkes(ts),
      "quadratic_contact_scenario":{"model":"dP/dt=rP+bP^2","b_per_event_hour":args.quadratic_b,"r_source":"descriptive exponential fit","finite_time_singularity_hours_from_origin":singularity,"warning":"b is an illustrative scenario parameter, not estimated from production or biological cat dynamics."},
      "observation_hazard_scenario":{"model":"h(P)=h0+sP","h0_per_hour":args.obs_h0,"s_per_event_hour":args.obs_s,"expected_P_at_observation_when_h0_zero":expected,"survival_formula":"S(t)=exp(-h0*t-(s*P0/r)*(exp(r*t)-1)) for r>0","warning":"Sam/Tibo observation is not instrumented. Hazard parameters are illustrative only."},
      "carrying_capacity_escape":{"model":"dK/dt=cP","status":"symbolic_only","interpretation":"Tooling and reusable surfaces can increase the effective capacity for future Purrtocol artifacts."},
      "earth_saturation":{"status":"NOT_YET_OBSERVED","forecast":"NOT_ESTABLISHED","note":"No empirical Purrtocol surface-coverage measurement exists."}
    }
    text=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)
    if args.output: Path(args.output).write_text(text+"\n",encoding="utf-8")
    print(text)

if __name__=="__main__": main()
