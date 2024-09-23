Please read this text before begin using these codes.

This direct contain python scripts which are used to calculate resonance raman spectrum based on gausssian16.
Before using the python scripts you need to open file calculat_set.txt and change valuable there according 
to your wish.

At the same time you need to copy molecule_name.xyz(A *.xyz file Template will show below) to current path.

File 'gen_s0_and_s1_freq.py' will generate s0_freq and s1_freq gaussain job file which are needed in resonance 
raman spectrum calculating.

It is highly recommand to using multiwfn to generate *.xyz file. 

After complish s0_freq and s1_freq job, you can use file 'gen_resonance_raman.py' to generate 
molecule_name_resonance_raman.gjf.Detail calculation infomation is in file rr_ser.txt. 
You should change it according to the hints.

Attention!!! Here is a template for *.xyz file \
Attention!!! molecule_name.xyz must exist when you using both of the python scripts.
WARNING!!! Do not add '\n' in the last of *.xyz file
WARNING!!! There must two lines before atom coordinates


58
generate by multiwfn
H 1.1 1.1 1.1
H 1.2 1.2 1.2\n
