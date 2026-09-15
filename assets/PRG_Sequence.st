(* Program-section fragment, not a full importable project.
   Locals: Step : UINT; Cyl01 : FB_Cylinder2Coil;
   Required caller/global BOOLs: Enable, Reset, StartNewPart, DestinationSensor,
   HomeSensor, WorkSensor, PermitHome, PermitWork, BeltRun, HomeValve, WorkValve.
   UDINTs: TaskCycleMs, CylinderTimeoutMs. All physical mapping is project-owned.
   Example cycle: feed, extend, retract, await next part.
   StartNewPart must be the template's rearmed new-part event, not a held sensor.
   Transitional Step lives HERE, not inside the cylinder FB. *)
IF NOT Enable THEN
    Step := 0;
ELSIF Reset AND ((Step = 0) OR (Step = 900)) AND HomeSensor AND NOT WorkSensor AND NOT DestinationSensor AND NOT Cyl01.Fault THEN
    Step := 10;
ELSIF Cyl01.Fault THEN
    Step := 900;
ELSE
    CASE Step OF
        10: IF StartNewPart THEN Step := 20; END_IF;
        20: IF DestinationSensor THEN Step := 30; END_IF;
        30: IF WorkSensor AND NOT HomeSensor THEN Step := 40; END_IF;
        40: IF HomeSensor AND NOT WorkSensor THEN Step := 10; END_IF;
        0, 900: ;
        ELSE Step := 900;
    END_CASE;
END_IF;
(* Compute commands AFTER transitions: arrival stops belt and requests Work now. *)
BeltRun := Enable AND (Step = 20) AND NOT Cyl01.Fault;
Cyl01(Enable := Enable, Reset := Reset,
    CmdWork := (Step = 30), CmdHome := (Step = 40),
    PermitWork := PermitWork, PermitHome := PermitHome,
    HomeSensor := HomeSensor, WorkSensor := WorkSensor,
    CycleMs := TaskCycleMs, TimeoutMs := CylinderTimeoutMs,
    HomeValve => HomeValve, WorkValve => WorkValve);
IF Cyl01.Fault THEN BeltRun := FALSE; Step := 900; END_IF;
