// Copiado a un checkout TEMPORAL de Shanhai para el benchmark de la etapa 0.
// No se adopta su arquitectura ni se importan módulos al proyecto.
import { describe, expect, it } from "vitest";
import { createSimulation } from "../../src/sim/simulation";
import { stableDefaultParams } from "../../src/sim/params";

function sum(a: ArrayLike<number>): number {
  let total=0;for(let i=0;i<a.length;i++)total+=a[i];return total;
}
const horizon=120;
describe("external world-research fit: hydrology and coupling",()=>{
  it("source ablation changes hydrology without changing the initial terrain",()=>{
    const wet=createSimulation("riverValleyGrassland",stableDefaultParams);
    const dry=createSimulation("riverValleyGrassland",stableDefaultParams);
    // Ablation must remove the real input: spring.output, when present,
    // overrides params.springOutput[season]. Changing only params did NOT
    // stop input in the first CI run. Keep all other initial state identical.
    dry.state.springs=[];
    const initialHeight=Array.from(wet.state.heightMap);
    expect(initialHeight).toEqual(Array.from(dry.state.heightMap));
    wet.step(horizon);
    dry.step(horizon);
    const wetSource=sum(wet.state.hydrologySource);
    const drySource=sum(dry.state.hydrologySource);
    // Last tick's source is enough to tell whether actual input exists.
    expect(wetSource).toBeGreaterThan(drySource);
    expect(drySource).toBe(0);
    expect(Array.from(wet.state.heightMap)).toEqual(initialHeight);
    expect(Array.from(dry.state.heightMap)).toEqual(initialHeight);
    const result={
      candidate:"Shanhai",
      stage:"ecology_hydrology",
      scenario:"riverValleyGrassland",
      ticks:horizon,
      waterWithSources:sum(wet.state.water),
      waterWithoutSources:sum(dry.state.water),
      totalMoistureWithSources:sum(wet.state.moisture),
      totalMoistureWithoutSources:sum(dry.state.moisture),
      plantBiomassWithSources:sum(wet.state.plantBiomass),
      plantBiomassWithoutSources:sum(dry.state.plantBiomass),
      terrainMutates:false,
      dryLastTickSource:drySource,
      ablation:"removed spring sources from otherwise identical initial state",
      wetLastTickSource:wetSource
    };
    console.log("WORLD_EVAL_JSON "+JSON.stringify(result));
  });

  it("same scenario reproduces full hydrology and vegetation arrays",()=>{
    const a=createSimulation("basinSpill",stableDefaultParams);
    const b=createSimulation("basinSpill",stableDefaultParams);
    a.step(100);b.step(100);
    expect(Array.from(a.state.water)).toEqual(Array.from(b.state.water));
    expect(Array.from(a.state.moisture)).toEqual(Array.from(b.state.moisture));
    expect(Array.from(a.state.plantBiomass)).toEqual(Array.from(b.state.plantBiomass));
    expect(Array.from(a.state.heightMap)).toEqual(Array.from(b.state.heightMap));
    // Read-only snapshot semantics: inspect alias as evidence, do not assert
    // one way or the other since upstream may change.
    const snap=a.getSnapshot();
    console.log("WORLD_EVAL_JSON "+JSON.stringify({
      candidate:"Shanhai",
      scenario:"basinSpill",
      ticks:100,
      replayEqual:true,
      snapshotHeightSharesBackingArray: snap.H === a.state.heightMap,
      snapshotWaterSharesBackingArray: snap.W === a.state.water,
      runtimeGrid: [a.state.width,a.state.height],
      maxTerrainClass: Math.max(...a.state.heightMap)
    }));
  });
});
