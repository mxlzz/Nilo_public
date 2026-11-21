// Injected temporarily at the END of upstream Sandspiel crate/src/lib.rs by the
// comparison workflow. Upstream source is not committed or modified in our project.
// Uses private fields ONLY for instrumentation: not evidence of public API fit.
#[cfg(test)]
mod candidate_eval {
    use super::*;

    fn sand_coordinates(universe: &Universe) -> Vec<(i32,i32)> {
        let mut coords=Vec::new();
        for x in 0..universe.width() {
            for y in 0..universe.height() {
                if universe.get_cell(x,y).species == Species::Sand { coords.push((x,y)); }
            }
        }
        coords
    }

    fn prepared() -> Universe {
        let mut u=Universe::new(24,24);
        // For native/headless integration, explicitly normalize the wind field.
        // Upstream constructor initializes dx/dy=0, while blow_wind interprets 126 as zero drift.
        for w in u.winds.iter_mut() { *w = Wind { dx: 126, dy: 126, pressure: 0, density: 0 }; }
        u.paint(12,4,0,Species::Sand);
        u
    }

    #[test]
    fn candidate_eval_sand_moves_down_and_is_not_lost() {
        let mut u=prepared();
        let before=sand_coordinates(&u);
        assert_eq!(before,vec![(12,4)]);
        for step in 0..12 {u.tick(); println!("EVIDENCE sand_step={} position={:?}",step+1,sand_coordinates(&u));}
        let after=sand_coordinates(&u);
        assert_eq!(after.len(),1,"sand conservation failed");
        assert!(after[0].1 > before[0].1, "sand did not descend");
        println!("EVIDENCE sand_position_before={:?} after={:?}",before,after);
    }

    #[test]
    fn candidate_eval_same_initial_state_same_result() {
        let mut u=prepared();
        let mut v=prepared();
        for _ in 0..20 {u.tick();v.tick();}
        assert_eq!(u.cells,v.cells);
        println!("EVIDENCE deterministic_same_input_20_ticks=true");
    }

    #[test]
    fn candidate_eval_uninitialized_wind_is_not_neutral() {
        let mut raw=Universe::new(24,24);
        raw.paint(12,4,0,Species::Sand);
        raw.tick();
        let pos=sand_coordinates(&raw);
        assert_eq!(pos.len(),1);
        println!("EVIDENCE raw_default_wind_sand_position_after_tick={:?}",pos);
        // Negative diagonal movement is the observed behavior for the raw default.
        assert!(pos[0].0 < 12 && pos[0].1 < 4);
    }

    #[test]
    fn candidate_eval_barrier_blocks_vertical_passage() {
        let mut u=prepared();
        for x in 0..24{u.paint(x,10,0,Species::Wall);}
        for _ in 0..20 {u.tick();}
        let after=sand_coordinates(&u);
        assert_eq!(after.len(),1,"sand not conserved against barrier");
        assert!(after[0].1<10, "sand passed through wall");
        println!("EVIDENCE sand_after_20_ticks_with_wall={:?}",after);
    }
}
