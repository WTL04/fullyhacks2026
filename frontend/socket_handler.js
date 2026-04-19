const socket = io();

socket.on('connect', () => {
    console.log('Socket connected:', socket.id);
});

function sendAction(type, target, value) {
    socket.emit('user_action', { type, target, value });
}

export { socket, sendAction };