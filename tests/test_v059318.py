"""0.5.9.3.18: condiciones autoestablecidas y filtros de lectura."""
import unittest
from pathlib import Path

from agenda import (normalize_task,set_agenda,awaken_reminders,
                    acknowledge_reminders,choose_agenda_step)
from project_lifecycle import retire_project
from brain import context_for,compact_context
from nilo import initial_state
from survival import ensure_needs

ROOT=Path(__file__).resolve().parent.parent


def reminder(threshold=60):
    return {"modo":"recordatorio","titulo":"Repetir comparación de descanso",
            "motivo":"La energía inicial de un ensayo comparable debe ser baja",
            "cuando":{"tipo":"cuando_necesidad","necesidad":"energia",
                      "menor_que":threshold}}


class ConditionedReminders(unittest.TestCase):
    def setUp(self):
        self.s=initial_state(731)
        self.p=self.s["person"]
        ensure_needs(self.p)["energia"]=75
        self.project={"id":"proyecto-ensayo","title":"Comparar descanso",
                      "status":"activo","progress":35}
        self.p["project"]=self.project
        self.p["projects"]=[]
        self.p["agenda"]=[]

    def test_wait_no_automatic_physical_step(self):
        task=normalize_task(reminder(),100,"proyecto-ensayo")
        self.assertEqual(task["modo"],"recordatorio")
        self.assertEqual(task["pasos"],[])
        self.assertEqual(task["cuando"]["menor_que"],60)
        self.p["agenda"].append(task)
        self.assertEqual(awaken_reminders(self.p,"Día 1"),[])
        self.assertIsNone(choose_agenda_step(self.s["world"],self.p))
        self.assertEqual(task["estado"],"pendiente")

    def test_crossing_threshold_notifies_once(self):
        task=set_agenda(self.p,[reminder()],100,self.project["id"])[0]
        self.p["needs"]["energia"]=59
        self.assertEqual(awaken_reminders(self.p,"Día 2"),[task])
        self.assertEqual(task["estado"],"lista_para_revisar")
        self.assertEqual(awaken_reminders(self.p,"Día 2"),[])
        self.assertIsNone(choose_agenda_step(self.s["world"],self.p))
        self.assertEqual(self.project["status"],"activo")

    def test_pause_keeps_reminder_pending_and_resume_acknowledges(self):
        task=set_agenda(self.p,[reminder()],100,self.project["id"])[0]
        retire_project(self.p,self.project,"pausado","Día 2",reason="Pendiente de energía")
        self.assertEqual(self.project["status"],"pausado")
        self.assertEqual(task["estado"],"pendiente")
        self.p["needs"]["energia"]=59
        awaken_reminders(self.p,"Día 3")
        acknowledge_reminders(self.p,self.project["id"],"Día 3")
        self.assertEqual(task["estado"],"completada")
        self.assertEqual(awaken_reminders(self.p,"Día 3"),[])

    def test_reminder_is_not_rewritten_by_ordinary_task(self):
        t=set_agenda(self.p,[reminder(),reminder()],100,self.project["id"])
        self.assertEqual(len(t),1)
        ordinary={"titulo":"Dormir","cuando":{"tipo":"cuando_necesidad","necesidad":"energia","menor_que":60},
                  "pasos":[{"op":"rest"}]}
        self.assertEqual(len(set_agenda(self.p,[ordinary],100,self.project["id"])),1)
        self.assertEqual(len(self.p["agenda"]),2)

    def test_reminder_does_not_accept_hidden_actions(self):
        wrong=reminder()
        wrong["pasos"]=[{"op":"rest"}]
        self.assertIsNone(normalize_task(wrong,100,self.project["id"]))

    def test_availability_survives_compact_context(self):
        task=set_agenda(self.p,[reminder()],100,self.project["id"])[0]
        self.p["needs"]["energia"]=59
        awaken_reminders(self.p,"Día 3")
        ctx=context_for(self.s["world"],self.p,[],"Día 3")
        self.assertEqual(ctx["recordatorios_listos"][-1]["id"],task["id"])
        compressed=compact_context(ctx,char_budget=1700)
        self.assertEqual(compressed["recordatorios_listos"][-1]["id"],task["id"])


class InterfaceStatusFilters(unittest.TestCase):
    def test_filter_and_indicator_share_one_toolbar(self):
        html=(ROOT/"interfaz.html").read_text("utf-8")
        self.assertIn('id="status-filter-wrap"',html)
        self.assertIn('id="indicator-inline"',html)
        self.assertIn("function matchesStatusView(record,section)",html)
        self.assertIn(".read-actions{display:flex;align-items:center;flex-wrap:nowrap",html)
        self.assertIn("nilo.statusViews.v1",html)
        self.assertIn("['agenda','projects'].includes(tab)",html)
        self.assertIn("recordatorio",html)


if __name__=="__main__":
    unittest.main()
