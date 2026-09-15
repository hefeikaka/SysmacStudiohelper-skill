"""Optional actual ST execution test. Supply your independently obtained Jiecc 7.x."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jiecc',required=True,type=Path);a=p.parse_args()
    source=(Path(__file__).resolve().parents[1]/'assets/FB_Cylinder2Coil.iec').read_text(encoding='utf-8')
    # Drive the delivered FB, not a separate behavioral model.
    body='''
U(Enable:=TRUE, CmdWork:=TRUE, PermitWork:=TRUE, CycleMs:=10, TimeoutMs:=20);
IF NOT U.WorkValve OR U.HomeValve THEN Failures:=Failures+1; END_IF;
U(WorkSensor:=TRUE);
IF NOT U.AtWork OR U.Busy THEN Failures:=Failures+1; END_IF;
U(CmdWork:=FALSE, CmdHome:=TRUE, PermitHome:=TRUE, WorkSensor:=FALSE);
IF NOT U.HomeValve OR U.WorkValve THEN Failures:=Failures+1; END_IF;
U(HomeSensor:=TRUE);
IF NOT U.AtHome OR U.Busy THEN Failures:=Failures+1; END_IF;
U(CmdWork:=TRUE);
IF NOT U.Fault OR U.HomeValve OR U.WorkValve OR U.FaultID<>3 THEN Failures:=Failures+1; END_IF;
U(CmdWork:=FALSE, CmdHome:=FALSE, Reset:=TRUE);
IF U.Fault THEN Failures:=Failures+1; END_IF;
U(Reset:=FALSE, HomeSensor:=FALSE, CmdWork:=TRUE);
U(); U(); U();
IF NOT U.Fault OR U.FaultID<>4 THEN Failures:=Failures+1; END_IF;
U(Enable:=FALSE);
IF U.HomeValve OR U.WorkValve THEN Failures:=Failures+1; END_IF;
V(Enable:=TRUE, HomeSensor:=TRUE, WorkSensor:=TRUE, CycleMs:=10, TimeoutMs:=20);
IF NOT V.Fault OR V.FaultID<>2 THEN Failures:=Failures+1; END_IF;
W(Enable:=TRUE, CycleMs:=0, TimeoutMs:=20);
IF NOT W.Fault OR W.FaultID<>1 THEN Failures:=Failures+1; END_IF;
'''
    sequence=(Path(__file__).resolve().parents[1]/'assets/PRG_Sequence.st').read_text(encoding='utf-8')
    body+='\nEnable:=TRUE; Reset:=TRUE; HomeSensor:=TRUE; PermitWork:=TRUE; PermitHome:=TRUE; TaskCycleMs:=10; CylinderTimeoutMs:=100;\n'+sequence
    body+='\nIF Step<>10 THEN Failures:=Failures+1; END_IF;\nReset:=FALSE; StartNewPart:=TRUE;\n'+sequence
    body+='\nIF NOT BeltRun OR WorkValve THEN Failures:=Failures+1; END_IF;\nStartNewPart:=FALSE; DestinationSensor:=TRUE;\n'+sequence
    body+='\nIF BeltRun OR NOT WorkValve OR Step<>30 THEN Failures:=Failures+1; END_IF;\n'
    decl='\nStep : UINT; Cyl01 : FB_Cylinder2Coil; TaskCycleMs : UDINT; CylinderTimeoutMs : UDINT;\n'
    decl+='\n'.join(n+' : BOOL;' for n in ['Enable','Reset','StartNewPart','DestinationSensor','HomeSensor','WorkSensor','PermitHome','PermitWork','BeltRun','HomeValve','WorkValve'])
    harness=source+'\nPROGRAM __main__\nVAR\nU : FB_Cylinder2Coil; V : FB_Cylinder2Coil; W : FB_Cylinder2Coil; Failures : DINT;'+decl+'\nEND_VAR\n//{st}\n'+body+'\n//{end}\nEND_PROGRAM\n'
    with tempfile.TemporaryDirectory() as directory:
        f=Path(directory)/'harness.iec';f.write_text(harness,encoding='utf-8')
        run=subprocess.run([str(a.jiecc.resolve()),'--run',str(f),'--max-cycles','1','--strict-ir','--verbose'],capture_output=True,encoding='utf-8',timeout=90)
    output=run.stdout+'\n'+run.stderr
    values=re.findall(r'''\bfailures['"]?\s*:\s*(\d+)''',output,re.I)
    if run.returncode or not values or int(values[-1]):
        print(output);return 1
    print('PASS: 13 checks on actual cylinder FB and program-section ST, including same-scan belt stop / Work command; NOT Sysmac compilation or simulation')
    return 0

if __name__=='__main__':raise SystemExit(main())
