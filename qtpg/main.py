from qtpg.program import Program

if __name__ == '__main__':
    program = Program(1, 5)
    state = (4, 2)
    print(program.execute(state))
