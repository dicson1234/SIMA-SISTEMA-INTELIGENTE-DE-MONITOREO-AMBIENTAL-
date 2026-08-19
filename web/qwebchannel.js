"use strict";

var QWebChannelMessageTypes = {
    signal: 1,
    propertyUpdate: 2,
    init: 3,
    idle: 4,
    debug: 5,
    invokeMethod: 6,
    connectToSignal: 7,
    disconnectFromSignal: 8,
    setProperty: 9,
    response: 10
};

var QWebChannel = function(transport, initCallback)
{
    if (typeof transport !== "object" || typeof transport.send !== "function") {
        console.error("The QWebChannel expects a transport object. Given is " + typeof transport, transport);
        return;
    }

    var channel = this;
    this.transport = transport;
    this.send = function(data) {
        if (typeof data !== "string") {
            data = JSON.stringify(data);
        }
        channel.transport.send(data);
    };

    this.transport.onmessage = function(message) {
        var data = (message && typeof message === "object" && "data" in message) ? message.data : message;
        if (typeof data === "string") {
            try { data = JSON.parse(data); } catch(e) {}
        }

        switch (data.type) {
            case QWebChannelMessageTypes.signal:
                channel.handleSignal(data);
                break;
            case QWebChannelMessageTypes.propertyUpdate:
                channel.handlePropertyUpdate(data);
                break;
            case QWebChannelMessageTypes.init:
                channel.handleInit(data);
                break;
            case QWebChannelMessageTypes.response:
                channel.handleResponse(data);
                break;
            default:
                console.error("invalid message received:", message.data);
                break;
        }
    };

    this.execCallbacks = {};
    this.execId = 0;
    this.objects = {};

    this.send({type: QWebChannelMessageTypes.init, id: 0});

    this.handleInit = function(data) {
        for (var objectName in data.objects) {
            new QObject(objectName, data.objects[objectName], channel);
        }

        for (var name in data.objects) {
            channel.objects[name].unwrapProperties();
        }

        if (initCallback) {
            initCallback(channel);
        }
    };

    this.handleSignal = function(data) {
        var object = channel.objects[data.object];
        if (object) {
            object.signalEmitted(data.signal, data.args);
        } else {
            console.warn("Unhandled signal of unknown object: " + data.object);
        }
    };

    this.handleResponse = function(data) {
        if (!data || data.id === undefined || data.id === null) {
            return;
        }
        if (data.id === 0 && data.data && typeof data.data === "object" && !channel.execCallbacks[0]) {
            channel.handleInit({ objects: data.data });
            return;
        }
        if (channel.execCallbacks[data.id]) {
            channel.execCallbacks[data.id](data.response !== undefined ? data.response : data.data);
            delete channel.execCallbacks[data.id];
        }
    };

    this.handlePropertyUpdate = function(data) {
        for (var i = 0; i < data.data.length; ++i) {
            var propertyUpdate = data.data[i];
            var object = channel.objects[propertyUpdate.object];
            if (object) {
                object.propertyUpdate(propertyUpdate.signals, propertyUpdate.properties);
            } else {
                console.warn("Unhandled property update of unknown object: " + propertyUpdate.object);
            }
        }
    };
};

function QObject(name, data, webChannel) {
    this.__id__ = name;
    webChannel.objects[name] = this;

    this.__webChannel__ = webChannel;

    var object = this;
    object.__propertyCache__ = {};

    var prop;
    for (prop in data.properties) {
        object.__propertyCache__[data.properties[prop][0]] = data.properties[prop][1];
    }

    for (prop in data.properties) {
        (function(propName, propValue) {
            Object.defineProperty(object, propName, {
                configurable: true,
                get: function() {
                    return object.__propertyCache__[propName];
                },
                set: function(value) {
                    if (value === undefined) {
                        console.warn("Property setter for " + propName + " called with undefined value!");
                        return;
                    }
                    object.__propertyCache__[propName] = value;
                    webChannel.send({
                        type: QWebChannelMessageTypes.setProperty,
                        object: object.__id__,
                        property: propName,
                        value: value
                    });
                }
            });
        })(data.properties[prop][0], data.properties[prop][1]);
    }

    var signal;
    for (signal in data.signals) {
        (function(signalName) {
            var signalIndex = data.signals[signal][0];
            object[signalName] = {
                connect: function(callback) {
                    if (typeof callback !== "function") {
                        console.error("Bad callback given to connect to signal " + signalName);
                        return;
                    }
                    object.__webChannel__.send({
                        type: QWebChannelMessageTypes.connectToSignal,
                        object: object.__id__,
                        signal: signalIndex
                    });
                    if (!object[signalName].callbacks) {
                        object[signalName].callbacks = [];
                    }
                    object[signalName].callbacks.push(callback);
                },
                disconnect: function(callback) {
                    if (typeof callback !== "function") {
                        console.error("Bad callback given to disconnect from signal " + signalName);
                        return;
                    }
                    if (!object[signalName].callbacks) {
                        return;
                    }
                    var idx = object[signalName].callbacks.indexOf(callback);
                    if (idx !== -1) {
                        object[signalName].callbacks.splice(idx, 1);

                        if (object[signalName].callbacks.length === 0) {
                            object.__webChannel__.send({
                                type: QWebChannelMessageTypes.disconnectFromSignal,
                                object: object.__id__,
                                signal: signalIndex
                            });
                        }
                    }
                }
            };
        })(data.signals[signal][0]);
    }

    var method;
    for (method in data.methods) {
        (function(methodName) {
            var methodIndex = data.methods[method][0];
            object[methodName] = function() {
                var args = [];
                var callback;
                for (var i = 0; i < arguments.length; ++i) {
                    if (typeof arguments[i] === "function") {
                        callback = arguments[i];
                    } else {
                        args.push(arguments[i]);
                    }
                }

                var id = object.__webChannel__.execId++;
                if (callback) {
                    object.__webChannel__.execCallbacks[id] = callback;
                }

                object.__webChannel__.send({
                    type: QWebChannelMessageTypes.invokeMethod,
                    object: object.__id__,
                    method: methodIndex,
                    args: args,
                    id: id
                });
            };
        })(data.methods[method][0]);
    }
}

QObject.prototype.unwrapProperties = function() {
    for (var prop in this.__propertyCache__) {
        var val = this.__propertyCache__[prop];
        if (Array.isArray(val)) {
            this.__propertyCache__[prop] = this.unwrapQObject(val);
        }
    }
};

QObject.prototype.unwrapQObject = function(response) {
    if (Array.isArray(response)) {
        for (var i = 0; i < response.length; ++i) {
            response[i] = this.unwrapQObject(response[i]);
        }
    } else if (typeof response === "object" && response !== null && response.id) {
        if (this.__webChannel__.objects[response.id]) {
            return this.__webChannel__.objects[response.id];
        }
    }
    return response;
};

QObject.prototype.signalEmitted = function(signalName, args) {
    if (this[signalName] && this[signalName].callbacks) {
        for (var i = 0; i < this[signalName].callbacks.length; ++i) {
            this[signalName].callbacks[i].apply(this[signalName], args);
        }
    }
};

QObject.prototype.propertyUpdate = function(signals, properties) {
    for (var prop in properties) {
        this.__propertyCache__[prop] = properties[prop];
    }
    for (var signalName in signals) {
        this.signalEmitted(signalName, signals[signalName]);
    }
};
