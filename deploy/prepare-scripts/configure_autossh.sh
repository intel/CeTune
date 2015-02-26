#!/usr/bin/expect

set remoteHost [lrange $argv 0 0]
set password [lrange $argv 1 1]

spawn scp /root/.ssh/id_rsa.pub $remoteHost:/
expect {
    "(yes/no)? " {
        send "yes\r"
        exp_continue
    }
    "password:" {
        send "${password}\r"
    }
}

interact {
    timeout 60 { send " "}
}

spawn ssh $remoteHost "cd /; cat id_rsa.pub >> /root/.ssh/authorized_keys"
expect {
    "password:" {
        send "${password}\r"
    }
}

interact {
    timeout 60 { send " "}
}


exit

