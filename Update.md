# Update

## Function System 

    Added a function system to .oct parser to define a global function that can be used by the commands. 

    It makes the code less complex and avoid code repetition.

    Syntax: 
        function Function_name ( arguments:list ) {
            system "start $argument[0]"
            response "$argument[1]"
        }

        ```
        Here `$` sign represents python string formatter (f'') 

        for word connected to `$variable_name` sign will be treated as variable and hence put inside string like (f"{variable_name}")
        
        so "start $argument[0]" in python will be taken as "os.system(f"start {argument[0]}")"
        ```

    Use case: 
        multiple commands uses same parameters and responses 
        eg:
            command "open notepad"{
                system "start notepad"
                response "Started Notepad!"
            }

            command "open paint"{
                system "start paint"
                response "Started Paint!"
            }

            command "open cmd"{
                system "start cmd"
                response "Started Command Prompt!"
            }

            #function can be utilized here as follow: 

            function open ( arguments:list ) {
                system "start $argument[0]"
                response "Started $argument[0]!"
            }

            Now these 3 commands can be written as:

            command "open notepad" uses open {
                "notepad",
                "Opened Notepad"
            }

            command "open paint" uses open {
                "paint",
                "Opened Paint"
            }

            command "open cmd" uses open {
                "cmd",
                "Opened Command Prompt!"
            }
            ```

        It makes the code less complex and avoid code repetition.

        