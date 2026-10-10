import unittest
from pathlib import Path
import subprocess

PDN = Path(__file__).resolve().parents[1] / 'pdn_ring.tcl'


class PDNConnectionTest(unittest.TestCase):
    def test_ring_uses_verified_m6_m7_grid_alignment(self):
        script = '''
proc set_voltage_domain args {}
proc define_pdn_grid args {}
proc add_pdn_stripe args {}
proc add_pdn_connect args {}
proc add_pdn_ring args {
    puts [lindex $args [expr {[lsearch -exact $args -spacings] + 1}]]
    puts [lindex $args [expr {[lsearch -exact $args -core_offsets] + 1}]]
}
namespace eval ord {
    proc get_core_area {} {return {0 0 20 20}}
    proc get_db_tech {} {return tech}
    proc microns_to_dbu {v} {return [expr {$v * 1000}]}
    proc dbu_to_microns {v} {return [expr {$v / 1000.0}]}
}
proc tech {method} {return 1}
source {%s}
''' % PDN
        result = subprocess.run(['tclsh'], input=script, text=True,
                                capture_output=True, check=True)
        self.assertEqual(result.stdout.splitlines(),
                         ['0.224 0.224', '0.484 0.528 0.532 0.522'])

    def test_m2_to_m5_via_stack_snaps_m4_pad_to_routing_tracks(self):
        text = PDN.read_text()
        self.assertIn(
            'add_pdn_connect -grid stdcells -layers {M2 M5} '
            '-min_width_layers {M3 M4} -ongrid {M4}', text
        )

    def test_intermediate_stack_layers_keep_minimum_width(self):
        text = PDN.read_text()
        self.assertIn(
            'add_pdn_connect -grid stdcells -layers {M2 M5} '
            '-min_width_layers {M3 M4}', text
        )

    def test_m6_m7_vias_space_cuts_by_the_drm_per_axis(self):
        text = PDN.read_text()
        self.assertIn(
            'add_pdn_connect -grid stdcells -layers {M6 M7} '
            '-cut_pitch {0.333 0.077}', text
        )

    def test_m5_straps_use_minimum_width_by_default(self):
        for override in (None, '0'):
            script = '''
proc set_voltage_domain args {}
proc define_pdn_grid args {}
proc add_pdn_stripe args {
    if {[lsearch -exact $args M5] >= 0} {
        puts [lindex $args [expr {[lsearch -exact $args -width] + 1}]]
    }
}
proc add_pdn_ring args {}
proc add_pdn_connect args {}
namespace eval ord {
    proc get_core_area {} {return {0 0 20 20}}
    proc get_db_tech {} {return tech}
    proc microns_to_dbu {v} {return [expr {$v * 1000}]}
    proc dbu_to_microns {v} {return [expr {$v / 1000.0}]}
}
proc tech {method} {return 1}
source {%s}
''' % PDN
            if override is not None:
                script = f'set ::env(SHA256_M5_MIN_WIDTH) {override}\n' + script
            result = subprocess.run(['tclsh'], input=script, text=True,
                                    capture_output=True, check=True)
            self.assertEqual(result.stdout.strip(), '0.024')


if __name__ == '__main__':
    unittest.main()
