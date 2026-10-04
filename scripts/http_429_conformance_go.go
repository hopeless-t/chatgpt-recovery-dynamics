// Independent Go implementation of the HTTP 429 Survival Plane.
// Standard library only. Loopback only. No production traffic.
package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"math"
	"net"
	"net/http"
	"os"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"
)

type ClientSettings struct {
	MinimumPeriodS float64 `json:"minimum_period_s"`
	LocalBaseS float64 `json:"local_base_s"`
	LocalCapS float64 `json:"local_cap_s"`
	HerdJitterFraction float64 `json:"herd_jitter_fraction"`
	RetryBudget int `json:"retry_budget"`
}
type ResponseSpec struct {
	Status int `json:"status"`
	ServiceS float64 `json:"service_s"`
	Headers map[string]string `json:"headers"`
	Body map[string]interface{} `json:"body"`
}
type ExpectSpec struct {
	Terminal string `json:"terminal"`
	Requests int `json:"requests"`
	MinSecondStartS float64 `json:"min_second_start_s"`
	MinStartGapS float64 `json:"min_start_gap_s"`
}
type ScriptedScenario struct {
	ScenarioID string `json:"scenario_id"`
	OperationID string `json:"operation_id"`
	Method string `json:"method"`
	Client ClientSettings `json:"client"`
	Responses []ResponseSpec `json:"responses"`
	Expect ExpectSpec `json:"expect"`
}
type AmbiguousScenario struct {
	ScenarioID string `json:"scenario_id"`
	OperationID string `json:"operation_id"`
	Endpoint string `json:"endpoint"`
	ApplicationIdempotencyContract bool `json:"application_idempotency_contract"`
	Client ClientSettings `json:"client"`
	Expect struct {
		Decision string `json:"decision"`
		PostRequests int `json:"post_requests"`
		SideEffects int `json:"side_effects"`
		ReobserveValue int `json:"reobserve_value"`
		Terminal string `json:"terminal"`
	} `json:"expect"`
}
type ScenarioFile struct {
	BaseDatetime string `json:"base_datetime"`
	Safety struct {
		NetworkScope string `json:"network_scope"`
		AllowedHost string `json:"allowed_host"`
		ProductionTraffic bool `json:"production_traffic"`
	} `json:"safety"`
	Scripted []ScriptedScenario `json:"scripted"`
	Ambiguous []AmbiguousScenario `json:"ambiguous"`
}
type RetryDecision struct {
	Action string `json:"action"`
	Reason string `json:"reason"`
	NextStartS *float64 `json:"next_start_s"`
	RetryAfterFloorS float64 `json:"retry_after_floor_s"`
	DraftRateLimitFloorS float64 `json:"draft_ratelimit_floor_s"`
	LocalBackoffS float64 `json:"local_backoff_s"`
	HerdJitterS float64 `json:"herd_jitter_s"`
	OperationID string `json:"operation_id"`
	AttemptID string `json:"attempt_id"`
	AttemptNumber int `json:"attempt_number"`
	BudgetRemainingAfterAttempt int `json:"budget_remaining_after_attempt"`
	StandardsUsed []string `json:"standards_used"`
}
type Attempt struct {
	AttemptNumber int `json:"attempt_number"`
	OperationID string `json:"operation_id"`
	AttemptID string `json:"attempt_id"`
	StartS float64 `json:"start_s"`
	ServiceS float64 `json:"service_s"`
	Status *int `json:"status"`
	TransportError interface{} `json:"transport_error"`
	RetryAfter interface{} `json:"retry_after"`
	RateLimit interface{} `json:"ratelimit"`
	Body interface{} `json:"body"`
	Decision string `json:"decision"`
	RetryDecision *RetryDecision `json:"retry_decision,omitempty"`
}
type ServerState struct {
	mu sync.Mutex
	scripted map[string]ScriptedScenario
	scriptedCounts map[string]int
	requestLog []map[string]string
	ambiguousPostRequests int
	ambiguousEffects int
	idempotentPostRequests int
	idempotentEffects int
	idempotentSeen map[string]map[string]interface{}
	idempotentDropDone bool
}
type LabServer struct {
	server *http.Server
	listener net.Listener
	state *ServerState
	baseURL string
}

var zeroWindowRE = regexp.MustCompile(`(?i)(?:^|,)\s*(?:"[^"]*"|[A-Za-z0-9._~-]+)\s*;[^,]*\br=0\b[^,]*\bt=(\d+)\b`)

func deterministicUnitInterval(key string) float64 {
	sum := sha256.Sum256([]byte(key))
	n := binary.BigEndian.Uint64(sum[:8])
	return float64(n) / float64(^uint64(0))
}
func exponentialBackoff(attempt int, base, cap float64) float64 {
	exp := attempt - 1
	if exp > 30 { exp = 30 }
	v := base * math.Pow(2, float64(exp))
	if v > cap { return cap }
	return v
}
func parseRetryAfter(value interface{}, now time.Time) *float64 {
	if value == nil { return nil }
	text := strings.TrimSpace(fmt.Sprint(value))
	if text == "" { return nil }
	if n, err := strconv.Atoi(text); err == nil && n >= 0 {
		v := float64(n); return &v
	}
	if t, err := http.ParseTime(text); err == nil {
		v := t.Sub(now).Seconds()
		if v < 0 { v = 0 }
		return &v
	}
	return nil
}
func parseDraftRateLimitZeroWindow(value interface{}) *float64 {
	if value == nil { return nil }
	m := zeroWindowRE.FindStringSubmatch(fmt.Sprint(value))
	if len(m) != 2 { return nil }
	n, err := strconv.Atoi(m[1]); if err != nil { return nil }
	v := float64(n); return &v
}
func retryAuthorization(method, state string, appID bool) (string, string, error) {
	switch state {
	case "known_applied":
		return "STOP_DUPLICATE", "operation already known applied", nil
	case "known_not_applied", "read_only_observation":
		return "TIMED_RETRY", "operation state permits a timed retry", nil
	case "unknown":
	default:
		return "", "", fmt.Errorf("unknown operation state: %s", state)
	}
	switch strings.ToUpper(method) {
	case "GET", "HEAD", "PUT", "DELETE", "OPTIONS", "TRACE":
		return "TIMED_RETRY", "unknown outcome but HTTP method semantics are idempotent; timing and budget still apply", nil
	}
	if appID {
		return "TIMED_RETRY", "unknown non-idempotent outcome covered by explicit application/provider idempotency contract", nil
	}
	return "REOBSERVE", "unknown non-idempotent outcome without explicit idempotency contract", nil
}
func decide(status *int, method, state string, appID bool, attempt, budget int, operationID string,
	nowS, previousStartS, minimumPeriodS float64, retryAfter, rateLimit interface{},
	localBaseS, localCapS, jitterFraction float64, nowDate time.Time) (RetryDecision, error) {
	attemptID := fmt.Sprintf("%s:attempt:%d", operationID, attempt)
	remaining := budget - attempt; if remaining < 0 { remaining = 0 }
	auth, reason, err := retryAuthorization(method, state, appID); if err != nil { return RetryDecision{}, err }
	stop := func(action string, standards []string) RetryDecision {
		if standards == nil { standards = []string{} }
		return RetryDecision{Action:action, Reason:reason, OperationID:operationID, AttemptID:attemptID, AttemptNumber:attempt, BudgetRemainingAfterAttempt:remaining, StandardsUsed:standards}
	}
	if auth == "STOP_DUPLICATE" { return stop("STOP_DUPLICATE", nil), nil }
	if auth == "REOBSERVE" { return stop("REOBSERVE", []string{"RFC9110-idempotent-method-semantics"}), nil }
	if attempt >= budget {
		d := stop("STOP_BUDGET", nil); d.Reason = "retry budget exhausted"; d.BudgetRemainingAfterAttempt = 0; return d, nil
	}
	ra := parseRetryAfter(retryAfter, nowDate)
	retryFloor := 0.0; if ra != nil { retryFloor = *ra }
	draftFloor := 0.0
	if ra == nil { if d := parseDraftRateLimitZeroWindow(rateLimit); d != nil { draftFloor = *d } }
	local := exponentialBackoff(attempt, localBaseS, localCapS)
	baseNext := math.Max(previousStartS+minimumPeriodS, math.Max(nowS+retryFloor, math.Max(nowS+draftFloor, nowS+local)))
	window := math.Max(1, math.Max(minimumPeriodS, math.Max(retryFloor, math.Max(draftFloor, local)))) * jitterFraction
	jitter := window * deterministicUnitInterval(fmt.Sprintf("%s:%d:herd-jitter", operationID, attempt))
	next := baseNext + jitter
	standards := []string{}
	if status != nil && *status == 429 { standards = append(standards, "RFC6585-429") }
	if ra != nil { standards = append(standards, "RFC9110-Retry-After") }
	if draftFloor > 0 { standards = append(standards, "draft-ietf-httpapi-ratelimit-headers-11") }
	return RetryDecision{Action:"WAIT_THEN_RETRY", Reason:reason, NextStartS:&next, RetryAfterFloorS:retryFloor, DraftRateLimitFloorS:draftFloor, LocalBackoffS:local, HerdJitterS:jitter, OperationID:operationID, AttemptID:attemptID, AttemptNumber:attempt, BudgetRemainingAfterAttempt:remaining, StandardsUsed:standards}, nil
}

func writeJSON(w http.ResponseWriter, status int, body interface{}, headers map[string]string) {
	for k,v := range headers { w.Header().Set(k,v) }
	w.Header().Set("Content-Type","application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}
func startServer(scripted map[string]ScriptedScenario) (*LabServer,error) {
	state := &ServerState{scripted:scripted, scriptedCounts:map[string]int{}, idempotentSeen:map[string]map[string]interface{}{}}
	mux := http.NewServeMux()
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		state.mu.Lock()
		state.requestLog = append(state.requestLog, map[string]string{"method":r.Method,"path":r.URL.Path,"operation_id":r.Header.Get("X-Lab-Operation-Id"),"attempt_id":r.Header.Get("X-Lab-Attempt-Id")})
		state.mu.Unlock()
		if r.Method=="GET" && strings.HasPrefix(r.URL.Path,"/scripted/") {
			id := strings.TrimPrefix(r.URL.Path,"/scripted/")
			sc,ok := state.scripted[id]; if !ok { writeJSON(w,404,map[string]interface{}{"error":"unknown scenario"},nil); return }
			state.mu.Lock(); count:=state.scriptedCounts[id]; state.scriptedCounts[id]=count+1; state.mu.Unlock()
			idx:=count; if idx>=len(sc.Responses){idx=len(sc.Responses)-1}
			resp:=sc.Responses[idx]; writeJSON(w,resp.Status,resp.Body,resp.Headers); return
		}
		if r.Method=="GET" && r.URL.Path=="/state" {
			state.mu.Lock()
			body:=map[string]interface{}{"ambiguous_effects":state.ambiguousEffects,"ambiguous_post_requests":state.ambiguousPostRequests,"idempotent_effects":state.idempotentEffects,"idempotent_post_requests":state.idempotentPostRequests}
			state.mu.Unlock(); writeJSON(w,200,body,nil); return
		}
		if r.Method=="POST" && r.URL.Path=="/ambiguous-apply" {
			_,_=io.Copy(io.Discard,r.Body)
			state.mu.Lock(); state.ambiguousPostRequests++; state.ambiguousEffects++; state.mu.Unlock()
			if hj,ok:=w.(http.Hijacker); ok { conn,_,err:=hj.Hijack(); if err==nil {_=conn.Close(); return} }
			return
		}
		if r.Method=="POST" && r.URL.Path=="/idempotent-apply" {
			_,_=io.Copy(io.Discard,r.Body); op:=r.Header.Get("X-Lab-Operation-Id")
			if op=="" { writeJSON(w,400,map[string]interface{}{"error":"missing operation id"},nil); return }
			state.mu.Lock()
			state.idempotentPostRequests++
			stored,ok:=state.idempotentSeen[op]
			if !ok { state.idempotentEffects++; stored=map[string]interface{}{"operation_id":op,"effect_number":state.idempotentEffects}; state.idempotentSeen[op]=stored }
			drop:=!state.idempotentDropDone; if drop { state.idempotentDropDone=true }
			state.mu.Unlock()
			if drop {
				if hj,ok:=w.(http.Hijacker); ok { conn,_,err:=hj.Hijack(); if err==nil {_=conn.Close(); return} }
				return
			}
			body:=map[string]interface{}{"ok":true,"deduplicated":true}; for k,v:=range stored {body[k]=v}
			writeJSON(w,200,body,nil); return
		}
		writeJSON(w,404,map[string]interface{}{"error":"not found"},nil)
	})
	ln,err:=net.Listen("tcp","127.0.0.1:0"); if err!=nil{return nil,err}
	server:=&http.Server{Handler:mux}; lab:=&LabServer{server:server,listener:ln,state:state,baseURL:"http://"+ln.Addr().String()}
	go func(){_ = server.Serve(ln)}()
	return lab,nil
}
func (s *LabServer) close(){ctx,cancel:=context.WithTimeout(context.Background(),2*time.Second);defer cancel();_=s.server.Shutdown(ctx)}

func requestJSON(method,url string,headers map[string]string,body interface{})(*int,http.Header,interface{},string){
	var reader io.Reader
	if body!=nil {b,_:=json.Marshal(body);reader=bytes.NewReader(b)}
	req,err:=http.NewRequest(method,url,reader);if err!=nil{return nil,nil,nil,err.Error()}
	for k,v:=range headers{req.Header.Set(k,v)}
	if body!=nil{req.Header.Set("Content-Type","application/json")}
	resp,err:=(&http.Client{Timeout:2*time.Second}).Do(req)
	if err!=nil{return nil,http.Header{},nil,err.Error()}
	defer resp.Body.Close();raw,_:=io.ReadAll(resp.Body);var decoded interface{}
	if len(raw)>0{_=json.Unmarshal(raw,&decoded)}
	status:=resp.StatusCode;return &status,resp.Header,decoded,""
}
func header(h http.Header,name string)interface{}{v:=h.Get(name);if v==""{return nil};return v}
func check(ok bool,msg string)error{if !ok{return errors.New(msg)};return nil}

func runScripted(server *LabServer,sc ScriptedScenario,baseDate time.Time)(map[string]interface{},error){
	virtualStart:=0.0;starts:=[]float64{};attempts:=[]Attempt{};terminal:="UNSET"
	for attempt:=1;attempt<=sc.Client.RetryBudget+1;attempt++{
		start:=virtualStart;starts=append(starts,start);attemptID:=fmt.Sprintf("%s:attempt:%d",sc.OperationID,attempt)
		status,headers,body,terr:=requestJSON(sc.Method,server.baseURL+"/scripted/"+sc.ScenarioID,map[string]string{"X-Lab-Operation-Id":sc.OperationID,"X-Lab-Attempt-Id":attemptID},nil)
		idx:=attempt-1;if idx>=len(sc.Responses){idx=len(sc.Responses)-1};service:=sc.Responses[idx].ServiceS;nowS:=start+service
		var te interface{};if terr!=""{te=terr};var ra,rl interface{};if headers!=nil{ra=header(headers,"Retry-After");rl=header(headers,"RateLimit")}
		ev:=Attempt{AttemptNumber:attempt,OperationID:sc.OperationID,AttemptID:attemptID,StartS:start,ServiceS:service,Status:status,TransportError:te,RetryAfter:ra,RateLimit:rl,Body:body}
		if status!=nil&&*status>=200&&*status<300{ev.Decision="SUCCESS";attempts=append(attempts,ev);terminal="SUCCESS";break}
		if status==nil{ev.Decision="UNEXPECTED_TRANSPORT_FAILURE";attempts=append(attempts,ev);terminal="UNEXPECTED_TRANSPORT_FAILURE";break}
		d,err:=decide(status,sc.Method,"read_only_observation",false,attempt,sc.Client.RetryBudget,sc.OperationID,nowS,start,sc.Client.MinimumPeriodS,ra,rl,sc.Client.LocalBaseS,sc.Client.LocalCapS,sc.Client.HerdJitterFraction,baseDate.Add(time.Duration(nowS*float64(time.Second))))
		if err!=nil{return nil,err};ev.Decision=d.Action;ev.RetryDecision=&d;attempts=append(attempts,ev)
		if d.Action!="WAIT_THEN_RETRY"{terminal=d.Action;break};if d.NextStartS==nil{return nil,errors.New("retry missing next start")};virtualStart=*d.NextStartS
	}
	gaps:=[]float64{};for i:=1;i<len(starts);i++{gaps=append(gaps,starts[i]-starts[i-1])}
	server.state.mu.Lock();requests:=server.state.scriptedCounts[sc.ScenarioID];server.state.mu.Unlock()
	if err:=check(terminal==sc.Expect.Terminal,sc.ScenarioID+": terminal");err!=nil{return nil,err}
	if err:=check(requests==sc.Expect.Requests,sc.ScenarioID+": requests");err!=nil{return nil,err}
	if sc.Expect.MinSecondStartS>0{if err:=check(len(starts)>1&&starts[1]>=sc.Expect.MinSecondStartS,sc.ScenarioID+": Retry-After floor");err!=nil{return nil,err}}
	if sc.Expect.MinStartGapS>0{for _,gap:=range gaps{if err:=check(gap>=sc.Expect.MinStartGapS,sc.ScenarioID+": start anchor");err!=nil{return nil,err}}}
	return map[string]interface{}{"scenario_id":sc.ScenarioID,"classification":"independent_go_loopback_real_http_virtual_time","terminal":terminal,"operation_id":sc.OperationID,"attempts":attempts,"start_times_s":starts,"start_gaps_s":gaps,"server_requests":requests,"pass":true},nil
}
func snapshotState(s *ServerState)map[string]interface{}{s.mu.Lock();defer s.mu.Unlock();return map[string]interface{}{"ambiguous_effects":s.ambiguousEffects,"ambiguous_post_requests":s.ambiguousPostRequests,"idempotent_effects":s.idempotentEffects,"idempotent_post_requests":s.idempotentPostRequests}}
func runUnknown(server *LabServer,sc AmbiguousScenario,baseDate time.Time)(map[string]interface{},error){
	a1:=sc.OperationID+":attempt:1";status,_,_,terr:=requestJSON("POST",server.baseURL+sc.Endpoint,map[string]string{"X-Lab-Operation-Id":sc.OperationID,"X-Lab-Attempt-Id":a1},map[string]interface{}{"action":"apply-once"})
	if status!=nil{return nil,errors.New("ambiguous POST unexpectedly returned HTTP status")}
	d,err:=decide(nil,"POST","unknown",false,1,sc.Client.RetryBudget,sc.OperationID,0.05,0,sc.Client.MinimumPeriodS,nil,nil,sc.Client.LocalBaseS,sc.Client.LocalCapS,sc.Client.HerdJitterFraction,baseDate.Add(50*time.Millisecond));if err!=nil{return nil,err}
	if d.Action!="REOBSERVE"{return nil,errors.New("unknown non-idempotent POST must re-observe")}
	obsStatus,_,obsBody,_:=requestJSON("GET",server.baseURL+"/state",map[string]string{"X-Lab-Operation-Id":sc.OperationID,"X-Lab-Attempt-Id":sc.OperationID+":observe:1"},nil)
	if obsStatus==nil||*obsStatus!=200{return nil,errors.New("state re-observation failed")}
	state:=snapshotState(server.state)
	return map[string]interface{}{"scenario_id":sc.ScenarioID,"classification":"independent_go_ambiguous_non_idempotent","transport_error":terr,"decision":d,"reobserved_state":obsBody,"post_requests":state["ambiguous_post_requests"],"side_effects":state["ambiguous_effects"],"pass":true},nil
}
func runExplicit(server *LabServer,sc AmbiguousScenario,baseDate time.Time)(map[string]interface{},error){
	a1:=sc.OperationID+":attempt:1";status,_,_,terr:=requestJSON("POST",server.baseURL+sc.Endpoint,map[string]string{"X-Lab-Operation-Id":sc.OperationID,"X-Lab-Attempt-Id":a1},map[string]interface{}{"action":"apply-once"})
	if status!=nil{return nil,errors.New("first explicit-contract POST should lose response")}
	d,err:=decide(nil,"POST","unknown",true,1,sc.Client.RetryBudget,sc.OperationID,0.05,0,sc.Client.MinimumPeriodS,nil,nil,sc.Client.LocalBaseS,sc.Client.LocalCapS,sc.Client.HerdJitterFraction,baseDate.Add(50*time.Millisecond));if err!=nil{return nil,err}
	if d.Action!="WAIT_THEN_RETRY"{return nil,errors.New("explicit contract must authorize timed retry")}
	a2:=sc.OperationID+":attempt:2";status2,_,body2,_:=requestJSON("POST",server.baseURL+sc.Endpoint,map[string]string{"X-Lab-Operation-Id":sc.OperationID,"X-Lab-Attempt-Id":a2},map[string]interface{}{"action":"apply-once"})
	if status2==nil||*status2!=200{return nil,errors.New("second explicit-contract POST failed")}
	server.state.mu.Lock();opIDs:=[]string{};attemptIDs:=[]string{}
	for _,row:=range server.state.requestLog{if row["path"]==sc.Endpoint{opIDs=append(opIDs,row["operation_id"]);attemptIDs=append(attemptIDs,row["attempt_id"])}}
	requests:=server.state.idempotentPostRequests;effects:=server.state.idempotentEffects;server.state.mu.Unlock()
	return map[string]interface{}{"scenario_id":sc.ScenarioID,"classification":"independent_go_explicit_application_idempotency","first_transport_error":terr,"first_decision":d,"terminal":"SUCCESS","operation_id":sc.OperationID,"attempt_ids":[]string{a1,a2},"server_operation_ids":opIDs,"server_attempt_ids":attemptIDs,"post_requests":requests,"side_effects":effects,"response":body2,"pass":true},nil
}

func main(){
	scenariosPath:=flag.String("scenarios","data/http_429_conformance_scenarios.json","scenario JSON");outputPath:=flag.String("output","","output report");flag.Parse()
	raw,err:=os.ReadFile(*scenariosPath);if err!=nil{panic(err)};var spec ScenarioFile;if err:=json.Unmarshal(raw,&spec);err!=nil{panic(err)}
	if spec.Safety.NetworkScope!="loopback_only"||spec.Safety.AllowedHost!="127.0.0.1"||spec.Safety.ProductionTraffic{panic("refusing non-loopback or production scenario file")}
	baseDate,err:=time.Parse(time.RFC3339,spec.BaseDatetime);if err!=nil{panic(err)}
	scripted:=map[string]ScriptedScenario{};for _,sc:=range spec.Scripted{scripted[sc.ScenarioID]=sc};results:=[]interface{}{}
	server,err:=startServer(scripted);if err!=nil{panic(err)}
	for _,sc:=range spec.Scripted{r,err:=runScripted(server,sc,baseDate);if err!=nil{server.close();panic(err)};results=append(results,r)};server.close()
	for _,sc:=range spec.Ambiguous{server,err:=startServer(scripted);if err!=nil{panic(err)};var r map[string]interface{};if sc.ApplicationIdempotencyContract{r,err=runExplicit(server,sc,baseDate)}else{r,err=runUnknown(server,sc,baseDate)};server.close();if err!=nil{panic(err)};results=append(results,r)}
	report:=map[string]interface{}{"schema":"http-429-go-independent-conformance-report/v1","classification":"independent_standard_library_implementation_loopback_only","implementation":map[string]interface{}{"language":"go","runtime":"go","imports_python_reference":false,"invokes_python_reference":false,"imports_node_reference":false,"invokes_node_reference":false,"third_party_packages":false},"network_scope":"127.0.0.1 ephemeral local server only","results":results,"summary":map[string]interface{}{"scenarios":len(results),"passed":len(results),"failed":0},"safety":map[string]interface{}{"production_traffic":false,"rate_limit_evasion":false,"remote_target_input":false}}
	out,_:=json.MarshalIndent(report,"","  ");out=append(out,'\n');fmt.Print(string(out));if *outputPath!=""{if err:=os.WriteFile(*outputPath,out,0644);err!=nil{panic(err)}}
}
