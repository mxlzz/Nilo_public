"""Instrument the upstream Powder Toy renderer *only in ephemeral CI checkout*.

The tiny harness is a read-only comparison, no own physics, and DOES NOT
copy third-party source into our repository. GPL-3 upstream code stays
inside GitHub runner workspace and is never uploaded as artifact.
Prerequisite: ETAPA_0_H15_PROTOCOLO_POWDER_TOY.md
"""
from pathlib import Path
import sys

def main(root):
    path=Path(root)/"src/PowderToyRenderer.cpp"
    s=path.read_text(encoding="utf-8")
    marker="int main(int argc, char *argv[])\n{"
    if s.count(marker)!=1:
        raise AssertionError("Expected upstream renderer main marker exactly once; record upstream drift")
    inject=r'''
int main(int argc, char *argv[])
{
    if (argc == 2 && std::string(argv[1]) == "--world-research-fit")
    {
        auto simulationData = std::make_unique<SimulationData>();
        struct Result
        {
            int startY, finalX, finalY, finalType, tick, dustCount;
        };
        auto trial = [](bool barrier) -> Result
        {
            auto sim = Simulation::Factory();
            sim->rng.seed(7321);
            auto x = XRES/2;
            auto y = YRES/3;
            if (barrier)
            {
                for (auto xx = x-50; xx<=x+50; ++xx)
                {
                    auto i=sim->create_part(-1,xx,y+3,PT_DMND);
                    if (i<0) throw std::runtime_error("Could not create barrier particle");
                }
            }
            auto id=sim->create_part(-1,x,y,PT_DUST);
            if (id<0) throw std::runtime_error("Could not create dust particle");
            for (auto frame=0; frame<15; ++frame)
            {
                sim->BeforeSim(true);
                sim->UpdateParticles(0,NPART);
                sim->AfterSim();
            }
            auto const &p = sim->parts[id];
            auto dust=0;
            for (auto idx=0; idx<sim->parts.active; ++idx)
                if (sim->parts[idx].type==PT_DUST) dust++;
            return {y,int(p.x+.5f),int(p.y+.5f),p.type,
                    sim->currentTick,dust};
        };
        auto free=trial(false);
        auto wall=trial(true);
        auto replay=trial(false);
        auto ok=free.finalType==PT_DUST
             && free.finalY>free.startY
             && wall.finalType==PT_DUST
             && wall.finalY<(wall.startY+3)
             && free.finalY>(free.startY+3)
             && wall.finalY<free.finalY
             && free.finalY==replay.finalY
             && free.finalX==replay.finalX
             && free.finalType==replay.finalType
             && free.tick==15 && wall.tick==15;
        std::cout
          << "WORLD_EVAL_JSON {"
          << "\"candidate\":\"The Powder Toy\","
          << "\"frames\":15,"
          << "\"dust_start_y\":" << free.startY << ","
          << "\"dust_free_final_y\":" << free.finalY << ","
          << "\"dust_free_final_x\":" << free.finalX << ","
          << "\"dust_wall_final_y\":" << wall.finalY << ","
          << "\"dust_wall_final_x\":" << wall.finalX << ","
          << "\"wall_y\":" << (wall.startY+3) << ","
          << "\"free_dust_count\":" << free.dustCount << ","
          << "\"wall_dust_count\":" << wall.dustCount << ","
          << "\"seeded_replay_equal\":" << (free.finalY==replay.finalY && free.finalX==replay.finalX ? "true":"false") << ","
          << "\"passed\":" << (ok?"true":"false")
          << "}" << std::endl;
        return ok?0:4;
    }
'''
    if '#include <stdexcept>' not in s:
        s=s.replace('#include <vector>','#include <vector>\n#include <string>\n#include <stdexcept>')
    if '#include "simulation/ElementClasses.h"' not in s:
        s=s.replace('#include "simulation/Simulation.h"',
                    '#include "simulation/Simulation.h"\n#include "simulation/ElementClasses.h"')
    path.write_text(s.replace(marker,inject,1),encoding="utf-8")
    print("H15 instrumented original render-only TPT source in temporary checkout; no upstream code copied to own repo",flush=True)

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: script PATH_TO_EPHEMERAL_UPSTREAM")
    main(sys.argv[1])
