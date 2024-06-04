import threading
import time

result_log = []
programs = []
threads = []


class MemorySystem:
    def __init__(self, num_registers, user_memory_rows, user_memory_cols, kernel_memory_rows, kernel_memory_cols,
                 secondary_storage_rows, secondary_storage_cols):
        self.registers = [0] * num_registers
        self.user_memory = [[0] * user_memory_cols for _ in range(user_memory_rows)]
        self.kernel_memory = [[0] * kernel_memory_cols for _ in range(kernel_memory_rows)]
        self.secondary_storage = [[0] * secondary_storage_cols for _ in range(secondary_storage_rows)]
        self.kernel_code = []
        self.page_table = {}
        self.pcb_list = []
        self.kernel_memory[2] = self.kernel_code
        self.kernel_memory[3] = self.page_table
        self.kernel_memory[4] = self.pcb_list

    def read_register(self, index):
        return self.registers[index]

    def write_register(self, index, value):
        self.registers[index] = value

    def read_user_memory(self, row, col):
        return self.user_memory[row][col]

    def write_user_memory(self, row, col, value):
        self.user_memory[row][col] = value

    def read_kernel_memory(self, row, col):
        return self.kernel_memory[row][col]

    def write_kernel_memory(self, row, col, value):
        self.kernel_memory[row][col] = value

    def read_secondary_storage(self, row, col):
        return self.secondary_storage[row][col]

    def write_secondary_storage(self, row, col, value):
        self.secondary_storage[row][col] = value

    def boot(self):
        print("Booting the system...")
        self.load_program_from_secondary_storage(2, self.kernel_code)
        self.load_program_from_secondary_storage(3, self.page_table)
        self.load_program_from_secondary_storage(4, self.pcb_list)
        print("System booted successfully.\n")

    def load_kernel_code_to_cpu(self):
        print("Loading kernel code to CPU...")
        self.registers = self.kernel_code
        print("Kernel code loaded to CPU.\n")

    def load_program_from_secondary_storage(self, index, program_info):
        print(f"Loading program information from secondary storage index {index} to kernel memory...")
        self.kernel_memory[index] = program_info
        print("Program information loaded to kernel memory.\n")

    def record_program_information_to_kernel_space(self, program_name, program_info):
        print(f"Recording program information of {program_name} to kernel space...")
        self.page_table[program_name] = program_info
        print("Program information recorded to kernel space.\n")

    def update_kernel_mapping_table(self, program_name, program_info):
        print(f"Updating kernel mapping table for {program_name}...")
        self.page_table[program_name] = program_info
        print("Kernel mapping table updated.\n")

    def load_process_registers_to_cpu(self, pcb):
        print(f"Loading process registers of PID {pcb.pid} to CPU...")
        self.registers = pcb.registers
        print("Process registers loaded to CPU.\n")


class Program:
    def __init__(self, name):
        self.name = name
        self.threads = [1, 2]

    def run(self):
        print(f"Program '{self.name}' is running...")
        time.sleep(2)


class PCB:
    def __init__(self, pid, state, pc, sp):
        self.pid = pid
        self.state = state
        self.pc = pc
        self.sp = sp
        self.registers = []
        self.threads = []

    def change_state(self, new_state):
        self.state = new_state
        print(f'State of Process {self.pid} is changed to {new_state}.')


class TCB:
    def __init__(self, tid, state, pc, sp):
        self.tid = tid
        self.state = state
        self.pc = pc
        self.sp = sp

    def change_state(self, new_state):
        self.state = new_state
        print(f'State of Thread {self.tid} is changed to {new_state}.')

    def update_registers(self, new_registers):
        self.registers = new_registers


class PageTable:
    def __init__(self, process_id):
        self.process_id = process_id
        self.page_entries = {}

    def add_page_entry(self, page_number, frame_number):
        self.page_entries[page_number] = frame_number

    def remove_page_entry(self, page_number):
        if page_number in self.page_entries:
            del self.page_entries[page_number]

    def get_frame_number(self, page_number):
        return self.page_entries.get(page_number, None)


lock = threading.Lock()

current_pc, current_sp = None, None


def set_context(pc, sp):
    global current_pc, current_sp
    current_pc = pc
    current_sp = sp


def get_context():
    global current_pc, current_sp
    return current_pc, current_sp


def process_context_switch(old_pcb, new_pcb):
    global lock

    with lock:
        print(f"Process Context Switching: PID {old_pcb.pid} -> PID {new_pcb.pid}")
        old_pcb.change_state("Ready")
        old_pc, old_sp = get_context()
        new_pcb.change_state("Running")
        new_pc, new_sp = new_pcb.pc, new_pcb.sp
        set_context(new_pc, new_sp)

        time.sleep(1)


def thread_context_switch(old_tcb, new_tcb):
    global lock

    with lock:
        print(f"Thread Context Switching: TID {old_tcb.tid} -> TID {new_tcb.tid}")
        old_tcb.change_state("Ready")
        old_pc, old_sp = get_context()
        new_tcb.change_state("Running")
        new_pc, new_sp = new_tcb.pc, new_tcb.sp
        set_context(new_pc, new_sp)

        time.sleep(1)


def interrupt_handler():
    result = "Interrupt occurred! Handling interrupt..."
    print(result)
    return result


def load_programs_to_memory(memory_system, programs):
    for program in programs:
        memory_system.record_program_information_to_kernel_space(program.name, program)
        memory_system.update_kernel_mapping_table(program.name, program)


def create_pcb_and_tcb_for_programs(programs):
    pcbs = []
    for i, program in enumerate(programs, 1):
        pcb = PCB(i, "New", 0x1000 * i, 0x2000 * i)
        pcb.threads = [TCB(j, "New", 0x1100 * j, 0x2100 * j) for j in range(1, 3)]
        pcbs.append(pcb)
    return pcbs


def run(thread_id, program_name, programs):
    global result_log
    for program in programs:
        if program.name == program_name:
            result = f"Running program '{program.name}'..."
            print(result)
            if result not in result_log:
                result_log.append(result)
            run_thread(thread_id, program_name, programs)
            if result not in result_log:
                result_log.append(result)
            break


def run_thread(thread_id, program_name, programs):
    global result_log
    for program in programs:
        if program.name == program_name:
            for thread in program.threads:
                if thread.tid == thread_id:
                    result = f"Running thread {thread.tid} of program '{program.name}'..."
                    print(result)
                    if result not in result_log:
                        result_log.append(result)
                    time.sleep(1)
                    if result not in result_log:
                        result_log.append(result)
                    break
            break


def main():
    global result_log
    memory_system = MemorySystem(8, 128, 128, 64, 64, 256, 256)

    # 프로그램 객체 생성
    for program_name in ['A', 'B', 'C']:
        program = Program(program_name)
        program.threads = [TCB(j, "New", 0x1100 * j, 0x2100 * j) for j in range(1, 3)]
        programs.append(program)

    choice = input("Do you want to boot? (y/n): ")
    if choice.lower() == 'y':
        memory_system.boot()

        print("1. Handle interrupt.")
        print("2. Run program.")
        print("Enter '0' to exit.")
        while True:
            choice = input("Enter your choice: ")
            if choice == '1':
                result = interrupt_handler()
                result_log.append(result)
            elif choice == '2':
                program_name = input("Enter the program name to run (A, B, or C): ")
                thread_id = int(input("Which thread do you want to run? (1 or 2): "))
                if thread_id == 1 or thread_id == 2:
                    run(thread_id, program_name, programs)
            elif choice == '0':
                print("\nPrinting program results...")
                for result in result_log:
                    print(f'{result}\n')
                print("Exiting program.")
                break
            else:
                print("Invalid choice. Please enter a valid option.")


if __name__ == "__main__":
    main()
