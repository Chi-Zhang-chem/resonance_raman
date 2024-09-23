import os, re, time

curr_path = os.getcwd()

file_list = os.listdir(curr_path)

#get sub_job info
relative_path = input(r'Please input the relative path based on /share/home/chizhang/')
queue_name = input('Set queue name:')
CPU_num = input('Set CPU number:')

#sh template
head_template = '''
#BSUB -J {job_name}
#BSUB -q {q_name}
#BSUB -n {N_num}
#BSUB -R span[ptile=24]
#BSUB -o {job_name}-%J.out

export NPROC={N_num}
export g16root=/share/apps/gaussian/G16B01/AVX2
. /share/apps/gaussian/G16B01/AVX2/g16/bsd/g16.profile
/share/apps/scripts/g16 {input_file}

'''

#set search template
def search_calculate_level(file_content):
    mem = None 
    nproc = None
    method = None
    basis_set = None
    scrf = None
    charge_space_spin_multiplicity = None
    
    #expression to find info
    mem_pattern = re.compile(r'mem=\s*(\d+GB)')
    nproc_pattern = re.compile(r'nproc=\s*(\d+)')
    method_pattern = re.compile(r'method=\s*([a-zA-Z\d-]+)')
    basis_set_pattern = re.compile(r'basis_set=\s*([a-zA-Z\d-]+)')
    scrf_pattern = re.compile(r'(scrf=\s*\(.+\))')
    charge_space_spin_multiplicity = re.compile(r'charge and spin multiplicity =\s+(\d+\s\d+)')

    for line in file_content:
        if re.search(mem_pattern, line) != None:
            mem = re.search(mem_pattern, line).group(1)

        if re.search(nproc_pattern, line) != None:
            nproc = re.search(nproc_pattern, line).group(1)

        if re.search(method_pattern, line) != None:
            method = re.search(method_pattern, line).group(1)

        if re.search(basis_set_pattern, line) != None:
            basis_set = re.search(basis_set_pattern, line).group(1)

        if re.search(scrf_pattern, line) != None:
            scrf = re.search(scrf_pattern, line).group(1)  

        if re.search(charge_space_spin_multiplicity, line) != None:
            charge_space_spin_multiplicity = re.search(charge_space_spin_multiplicity, line).group(1)

    return mem, nproc, method, basis_set, scrf, charge_space_spin_multiplicity

#get RR set
def search_resonance_raman_settings(file_content):
    spectroscopy = None
    spectrum = None
    rr = None
    intermediate = None
    td = None
    print_settings = None
    
    # Compile regular expressions for each parameter
    spectroscopy_pattern = re.compile(r'Spectroscopy\s*=\s*(\w+)')
    spectrum_pattern = re.compile(r'Spectrum\s*=\s*\(([^)]+)\)')
    rr_pattern = re.compile(r'RR\s*=\s*\(([^)]+)\)')
    intermediate_pattern = re.compile(r'Intermediate\s*=\s*(\w+\s*=\s*\w+)')
    td_pattern = re.compile(r'TD\s*=\s*\(([^)]+)\)')
    print_pattern = re.compile(r'Print\s*=\s*\(([^)]+)\)')

    for line in file_content:
        if re.search(spectroscopy_pattern, line) != None:
            spectroscopy = re.search(spectroscopy_pattern, line).group(1)

    for line in file_content:
        if re.search(spectrum_pattern, line) != None:
            spectrum = re.search(spectrum_pattern, line).group(1) 

    for line in file_content:
        if re.search(rr_pattern, line) != None:
            rr = re.search(rr_pattern, line).group(1)

    for line in file_content:
        if re.search(intermediate_pattern, line) != None:
            intermediate = re.search(intermediate_pattern, line).group(1)
             
    for line in file_content:
        if re.search(td_pattern, line) != None:
            td = re.search(td_pattern, line).group(1)
             
    for line in file_content:
        if re.search(print_pattern, line) != None:
            print = re.search(print_pattern, line).group(1)

    return spectroscopy, spectrum, rr, intermediate, td, print

#get calculate setting
with open('calculate_set.txt', 'r', encoding='utf-8') as cal_info:
    file_content = cal_info.readlines()
    mem, nproc, method, basis_set, scrf, charge_space_spin_multiplicity = search_calculate_level(file_content)

#get resonance raman setting 
with open('RR_set.txt', 'r', encoding='utf-8') as RR_info:
    file_content_1 = RR_info.readlines()
    spectroscopy, spectrum, rr, intermediate, td, print = search_resonance_raman_settings(file_content_1)

#generate resonance_raman_gjf    
for file in file_list:
    if file.endswith(".xyz"):
        with open(file, 'r', encoding='utf-8') as f:
            file_content = f.readlines()
            molecule_name = file[:-4]

        with open(f'{molecule_name}_resonance_raman.gjf', 'w') as rr_gjf:
            rr_gjf.write(f'%mem={mem}\n')
            rr_gjf.write(f'%nproc={nproc}\n')
            rr_gjf.write(f'%chk={molecule_name}_s0_freq.chk\n')#Ground stare checkpoint file
            rr_gjf.write(f'#p {method} {basis_set} {scrf} Freq=(FC,ReadFC,ReadFCHT) geom=check guess=read \n\n')
            rr_gjf.write(f'{molecule_name}_resonance_raman_spectrum\n\n')
            rr_gjf.write(f'{charge_space_spin_multiplicity}\n\n')
            #ReadFCHT input 
            rr_gjf.write(f'Spectroscopy={spectroscopy}\n') #select resonance raman spectrum
            rr_gjf.write(f'Spectrum=({spectrum})\n') #set spectrum x range and how to broad(stick, gaussain, lorentzian)
            rr_gjf.write(f'RR=({rr})\n') #set incident light energy range in cm-1
            rr_gjf.write(f'Intermediate={intermediate}\n') #Get second state data from checkpoint file (named below) 
            rr_gjf.write(f'TD=({td})\n') #hard to understand...
            rr_gjf.write(f'Print=({print})\n\n') #print tensors and exchange-correlation matrix
            rr_gjf.write(f'{molecule_name}_s1_freq.chk') #Excited state checkpoint file

print('Gjf file have been created.')

#generate s0 and s1 sh file

plist = os.listdir(curr_path)     
count = 0 
batchFDU = f'cd /share/home/chizhang/{relative_path}\n'

for fname in plist:
    if fname.endswith('.com') or fname.endswith('.gjf'):
        count += 1

        # 生成 .sh 文件名
        sh_name = time.strftime("%m-%d-%H%M%S-", time.localtime()) + str(count).zfill(2) + fname[:-4] + '.sh'

        # 填充脚本模板
        head = head_template.format(job_name=fname[:-4], q_name=queue_name, N_num=CPU_num, input_file=fname)

        # 将生成的 .sh 文件写入指定目录
        with open(os.path.join(curr_path, sh_name), 'w') as f:
            f.write(head)

        # 生成批量提交的内容
        batchFDU += f"sed -i 's/\\r$//' {sh_name}\n"
        batchFDU += f"bsub < {sh_name} &\n"
       
# 将 batchFDU.txt 文件写入指定目录
with open(curr_path+'\\submit_s1_and_s0_gjf.txt', 'w') as f:
    f.write(batchFDU)

print(f"{count} *.sh files generated and submit_s1_and_s0_gjf.txt created.")