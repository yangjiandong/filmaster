
from difflib import SequenceMatcher

def html_diff( old, new ):
    seqm = SequenceMatcher( None, old, new )
    output= []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == 'equal':
            output.append(seqm.a[a0:a1])

        elif opcode == 'insert':
            output.append("<ins>" + seqm.b[b0:b1] + "</ins>")

        elif opcode == 'delete':
            output.append("<del>" + seqm.a[a0:a1] + "</del>")

        elif opcode == 'replace':
            output.append( "<del>"+ seqm.a[a0:a1] + "</del><ins>" + seqm.b[b0:b1] + "</ins>" )
        
    return ''.join(output)
