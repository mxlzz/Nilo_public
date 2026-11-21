"""H16A external site user-interface smoke only (public browser usage).

No source extraction, no private browser API, no copying website content/assets.
One session and one optional speed-control click. Only metrics of visible UI.
Preregistered: ETAPA_0_H16_PROTOCOLO_ECOSYSTEM_EXPLORER.md
"""
import json
import re
import time
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

URL="https://www.ethanjhulbert.org/ecosystem-explorer/"
YEAR_RE=re.compile(r"\bYear\s+(\d+)\s*[·.•\-]?\s*(Spring|Summer|Autumn|Fall|Winter)?",re.I)


def visible_summary(page):
    t=page.locator("body").evaluate("(el) => el.innerText.slice(0,12000)")
    match=YEAR_RE.search(t)
    return {
        "year":int(match.group(1)) if match else None,
        "season":match.group(2) if match and match.group(2) else None,
        "generating_label_visible":"Generating landscape" in t or "Preparing terrain" in t,
        "seed_input_label":"Seed" in t,
        "save_export_controls":("Export file" in t and "Save in browser" in t),
        "tile_inspector_label":"Tile inspector" in t,
        "surface_controls":("Terrain types" in t or "Map view" in t),
        "speed_controls":("28×" in t or "7×" in t),
        "declared_world_area_label":bool(re.search(r"\bWORLD\s+\d",t))
    }


def main():
    started=time.perf_counter()
    metrics={
        "test":"H16A Ecosystem Explorer single-user browser UI black-box baseline",
        "site":URL,
        "scope":"Visible controls and calendar only; not erosion, ecology, licensed source, seed or physical fidelity",
        "network_requests_not_logged":True,
        "code_assets_never_saved":True
    }
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={"width":1440,"height":900},locale="en-US")
        metrics["http_response_status"]=None
        try:
            response=page.goto(URL,wait_until="domcontentloaded",timeout=45000)
            metrics["http_response_status"]=response.status if response else None
            page.wait_for_timeout(7000)
            metrics["initial_visible"]=visible_summary(page)
            metrics["canvas_count"]=page.locator("canvas").count()
            metrics["speed_change_clicked"]=False
            metrics["speed_click_exception"]=None
            try:
                btn=page.get_by_role("button",name=re.compile(r"28×"))
                if btn.count()>0:
                    btn.first.click(timeout=4500)
                    metrics["speed_change_clicked"]=True
            except Exception as ex:
                metrics["speed_click_exception"]=type(ex).__name__+":"+str(ex)[:150]
            page.wait_for_timeout(15000)
            metrics["later_visible"]=visible_summary(page)
            a=metrics["initial_visible"];b=metrics["later_visible"]
            metrics["year_advanced"]= bool(
                a["year"] is not None and b["year"] is not None and
                b["year"]>a["year"]
            )
            metrics["season_or_year_changed"]= bool(
                a["year"] is not None and b["year"] is not None and (
                    a["year"]!=b["year"] or a["season"]!=b["season"]
                )
            )
            def visible_buttons():
                result=[]
                for elem in page.locator("button").all():
                    if elem.is_visible():
                        result.append({
                            "text":elem.inner_text()[:38],
                            "title":elem.get_attribute("title"),
                            "aria":elem.get_attribute("aria-label")
                        })
                return result[:26]
            metrics["visible_buttons"] = visible_buttons()
            metrics["new_world_panel_opened"]=False
            metrics["inspect_panel_opened"]=False
            metrics["panel_open_errors"]=[]
            try:
                star=page.get_by_role("button",name=re.compile(r"✳"))
                if star.count()>0:
                    star.first.click(timeout=5000)
                    page.wait_for_timeout(500)
                    metrics["new_world_panel"] = visible_summary(page)
                    metrics["new_world_panel_opened"]=(
                        metrics["new_world_panel"]["seed_input_label"] and
                        metrics["new_world_panel"]["save_export_controls"])
            except Exception as ex:
                metrics["panel_open_errors"].append("new_world:"+type(ex).__name__+":"+str(ex)[:120])
            if metrics["new_world_panel_opened"]:
                try:
                    close=page.get_by_role("button",name=re.compile(r"×"))
                    if close.count()>0: close.first.click(timeout=5000)
                except Exception as ex:
                    metrics["panel_open_errors"].append("close:"+type(ex).__name__+":"+str(ex)[:120])
            try:
                inspector=page.get_by_role("button",name=re.compile(r"⌖"))
                if inspector.count()>0:
                    inspector.first.click(timeout=5000)
                    page.wait_for_timeout(500)
                    metrics["inspector_panel"]=visible_summary(page)
                    metrics["inspect_panel_opened"]=metrics["inspector_panel"]["tile_inspector_label"]
            except Exception as ex:
                metrics["panel_open_errors"].append("inspector:"+type(ex).__name__+":"+str(ex)[:120])
            metrics["ui_controls_present"]= bool(
                b["speed_controls"] and metrics["new_world_panel_opened"]
                and metrics["inspect_panel_opened"]
            )
        finally:
            metrics["elapsed_seconds"]=round(time.perf_counter()-started,2)
            print("WORLD_EVAL_JSON "+json.dumps(metrics,sort_keys=True),flush=True)
            browser.close()
    assert metrics["http_response_status"]==200, "H16A site unavailable"
    assert metrics["ui_controls_present"], "H16A required controls not visible"
    assert metrics["season_or_year_changed"], "H16A simulated UI calendar not observed advancing"

if __name__=="__main__":
    main()
