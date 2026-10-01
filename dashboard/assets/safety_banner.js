// Stable callback name avoids hash changes when banner wording is edited.
window.dash_clientside = window.dash_clientside || {};
window.dash_clientside.weatherSafety = {
    renderWaitingPeriod: function(status, tick) {
    const style = {marginBottom:'5px', color:'white', fontSize:'28px',
                   textAlign:'center', padding:'10px', height:'auto', whiteSpace:'pre-line'};
    const waitingStyle = {...style, backgroundColor:'rgb(228, 130, 75)', color:'var(--bs-white)'};
    if (!status) return [false, 'Checking station safety status…', waitingStyle];
    if (status.state === 'alert') {
        window.wsLastRedMessage = status.message;
        return [false, status.message, {...style, backgroundColor:'red'}];
    }
    if (status.state === 'unknown' && window.wsLastRedMessage) {
        return [false, window.wsLastRedMessage+'\nStation data unavailable — alert clearance cannot be verified.', {...style, backgroundColor:'red'}];
    }
    window.wsLastRedMessage = null;
    if (status.state === 'clear') return [true, '', style];
    let text = status.message;
    if (status.state === 'recovery') {
        // Anchor to the server clock; workstation clock offsets cannot shorten recovery.
        if (window.wsRecoverySnapshot !== status.server_now) {
            window.wsRecoverySnapshot = status.server_now;
            window.wsRecoveryReceived = performance.now();
        }
        const now = status.server_now + performance.now() - window.wsRecoveryReceived;
        const seconds = Math.max(0, Math.ceil((status.deadline-now)/1000));
        const minutes = String(Math.floor(seconds/60)).padStart(2,'0');
        const remainder = String(seconds%60).padStart(2,'0');
        const duration = status.duration_seconds / 60;
        text = duration+'-min waiting period — '+minutes+':'+remainder+' remaining after the last alert cleared';
    }
    return [false, text, waitingStyle];
}
};
