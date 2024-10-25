const daq_control_buttons = document.getElementsByClassName('btn-daq-control');
const selectable_run_types = document.getElementsByClassName('selectable-run-type')


function disable_daq_controls() {
    for (let i = 0; i < daq_control_buttons.length; i++) {
        daq_control_buttons[i].className += " disabled";
    }
}

function deselect_all_run_types() {
    for (let i = 0; i < selectable_run_types.length; i++) {
        selectable_run_types[i].selected = false;
    }
}

function enable_daq_controls() {
    for (let i = 0; i < daq_control_buttons.length; i++) {
        daq_control_buttons[i].className = daq_control_buttons[i].className.slice(0, -9);
    }
}
function disable_autopilot_form(disable = true, values = {}){
    if (values != {} && disable)
        update_autopilot_form(values);
    document.getElementById('user').disabled = disable;
    document.getElementById('notes').disabled = disable;
    document.getElementById('run-type').disabled = disable;
    document.getElementById('auto-run-restart').disabled = disable;
    document.getElementById('auto-run-length').disabled = disable;
}
function enable_autopilot_form(){
    disable_autopilot_form(false);
}
function update_autopilot_form(values){
    console.log(values)
    document.getElementById('user').value = values.user;
    document.getElementById('notes').value = values.run_notes;
    deselect_all_run_types();
    document.getElementById('run-type-'+String(values.run_type).replace(' ','-')).selected = true;
    document.getElementById('auto-run-restart').checked = values.autorestart;
    document.getElementById('auto-run-length').value = values.run_length;

}


function autopilot_enable() {
    socket.emit("autopilot_enable", {
        user: document.getElementById('user').value,
        run_type: document.getElementById('run-type').value,
        run_notes: document.getElementById('notes').value,
        autorestart: document.getElementById('auto-run-restart').value,
        run_length: document.getElementById('auto-run-length').value
    });
    update_autopilot_button(true);
    disable_autopilot_form();
}

function autopilot_disable() {
    socket.emit("autopilot_disable", function () { });
    update_autopilot_button(false);
    enable_autopilot_form();

}

function update_autopilot_button(autopilot_on) {
    if (autopilot_on) {
        document.getElementById("autopilot").onclick = autopilot_disable;
        document.getElementById("autopilot").innerHTML = document.getElementById("autopilot").innerHTML.slice(0, -6) + '"></i>';
        document.getElementById("autopilot").title = 'Deactivate Autopilot';
        document.getElementById("autopilot").className = "nav-item btn btn-light gap-4";
    } else {
        document.getElementById("autopilot").onclick = autopilot_enable;
        document.getElementById("autopilot").innerHTML = document.getElementById("autopilot").innerHTML.replace(/-fill/g, "");
        document.getElementById("autopilot").title = 'Activate Autopilot';
        document.getElementById("autopilot").className = "nav-item btn btn-outline-light gap-4";
    }
}


function send_event(event) {
    socket.emit(event, function () { });
    if (!document.getElementById(event).innerHTML.includes("-fill"))
        document.getElementById(event).innerHTML = document.getElementById(event).innerHTML.slice(0, -6)
            + '-fill"></i>';

    document.getElementById(event).className += " disabled";
}

function reset() {
    socket.emit("reset", function () { });
}

function update_buttons(button_status) {
    for (var key in button_status) {
        if (button_status[key].disabled && !document.getElementById(key).className.includes(" disabled")) {
            document.getElementById(button_status[key].event).className += " disabled";
        }

        if (!button_status[key].disabled) {
            document.getElementById(button_status[key].event).className = document.getElementById(key).className.replace(/ disabled/g, "");
        }
    }
}

function update_log(logs) {
    let htmlclass = "";
    let log_table = ""
    for (let i = 0; i < logs.length; i++) {
        htmlclass = "";
        console.log("Log entry");
        if (logs.type == "Error") {
            htmlclass = ' class="table-danger"';
        } else if (logs.type == "Warning") {
            htmlclass = ' class="table-warning"';
        }
        log_table = '<tr' + htmlclass + '><td>' + logs[i]["timestamp"] + '</td><td>' + logs[i]["message"] + '</td></tr>' + log_table;
    }
    document.getElementById("log-table-body").innerHTML = log_table
}

function enable_auto_run_length() {
    document.getElementById('auto-run-length').disabled = false;
    document.getElementById('auto-run-restart').checked = true;
    document.getElementById('auto-run-restart').onclick = disable_auto_run_length;
}

function disable_auto_run_length() {
    document.getElementById('auto-run-length').disabled = true;
    document.getElementById('auto-run-restart').checked = false;
    document.getElementById('auto-run-restart').onclick = enable_auto_run_length;
}
