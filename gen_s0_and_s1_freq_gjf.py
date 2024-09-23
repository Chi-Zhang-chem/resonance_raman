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
        if re.search(mem_pattern, line):
            mem = re.search(mem_pattern, line).group(1)

        if re.search(nproc_pattern, line):
            nproc = re.search(nproc_pattern, line).group(1)

        if re.search(method_pattern, line):
            method = re.search(method_pattern, line).group(1)

        if re.search(basis_set_pattern, line):
            basis_set = re.search(basis_set_pattern, line).group(1)

        if re.search(scrf_pattern, line):
            scrf = re.search(scrf_pattern, line).group(1)  

        if re.search(charge_space_spin_multiplicity, line):
            charge_space_spin_multiplicity = re.search(charge_space_spin_multiplicity, line).group(1)

    return mem, nproc, method, basis_set, scrf, charge_space_spin_multiplicity

#get calculate setting
with open('calculate_set.txt', 'r', encoding='utf-8') as cal_info:
    file_content = cal_info.readlines()
    mem, nproc, method, basis_set, scrf, charge_space_spin_multiplicity = search_calculate_level(file_content)

#generate s0 and s1 gjf
for file in file_list:
    if file.endswith(".xyz"):
        with open(file, 'r', encoding='utf-8') as f:
            file_content = f.readlines()
            molecule_name = file[:-4]
            atom_coordinate = file_content[2:]

        #generate s0_freq_gjf
        with open(f'{molecule_name}_s0_freq.gjf', 'w') as s0_gjf:
            s0_gjf.write(f'%mem={mem}\n')
            s0_gjf.write(f'%nporc={nproc}\n')
            s0_gjf.write(f'%chk={molecule_name}_s0_freq.chk\n')
            s0_gjf.write(f'#p {method} {basis_set} {scrf} opt freq=(raman,savenormalmodes)\n\n')
            s0_gjf.write(f'{molecule_name}_s0_freq\n\n')
            s0_gjf.write(f'{charge_space_spin_multiplicity}\n')
            for content in atom_coordinate:
                s0_gjf.write(f'{content}')
            s0_gjf.write('\n\n') 

        #generate s1_freq_gif
        with open(f'{molecule_name}_s1_freq.gjf', 'w') as s1_gjf:
            s1_gjf.write(f'%mem={mem}\n')
            s1_gjf.write(f'%nporc={nproc}\n')
            s1_gjf.write(f'%chk={molecule_name}_s1_freq.chk\n')
            s1_gjf.write(f'#p {method} {basis_set} {scrf} TD=(NStates=20,Root=1) Opt=CalcFC Freq=(raman,savenormalmodes) NoSymm\n\n')
            s1_gjf.write(f'{molecule_name}_s0_freq\n\n')
            s1_gjf.write(f'{charge_space_spin_multiplicity}\n')
            for content in atom_coordinate:
                s1_gjf.write(f'{content}')
            s1_gjf.write('\n') 
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