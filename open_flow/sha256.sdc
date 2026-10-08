# OpenROAD/OpenSTA-compatible constraints for the open-source baseline.
# Keep the original Innovus SDC in sdc/sha256.sdc unchanged.
current_design sha256
create_clock -name clk -period 600 [get_ports clk]
set_input_delay -clock clk 1 [all_inputs -no_clocks]
set_output_delay -clock clk 300 [all_outputs]
