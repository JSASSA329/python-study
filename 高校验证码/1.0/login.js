// 加密算法库
const Crypto = require('crypto-js')
// MD5加密
function _0x4c771b(arg){
    return Crypto.MD5(arg).toString()
}
// 随机生成字符串
function _0x11dbad() {
    // var _0x5c52a4 = _0x2e675c;
    for (var _0x55977e = [], _0x12474f = '0123456789abcdef', _0x33c6e8 = 0x0; _0x33c6e8 < 0x24; _0x33c6e8++)
        _0x55977e[_0x33c6e8] = _0x12474f['substr'](Math['floor'](0x10 * Math['random']()), 0x1);
    return _0x55977e[0xe] = '4',
        _0x55977e[0x13] = _0x12474f['substr'](0x3 & _0x55977e[0x13] | 0x8, 0x1),
        _0x55977e[0x8] = _0x55977e[0xd] = _0x55977e[0x12] = _0x55977e[0x17] = '-',
        _0x55977e['join']('');
}

// function _0x11dbad(){
//     return "bca67b94-7f69-42ae-9aa2-3d92d621f612"
// }

function get_params(_0x4e0309){

    // captchaId
    _0x3fedba = "qDG21VMg9qS5Rcok4cfpnHGnpf5LhcAv"
    _0x589b78 = "slide"

    // // 时间戳
    // _0x4e0309 = 1763400659382
    // // _0x4e0309 = Date.now()

    // captchaKey 参数生成
    _0x422ded = _0x4c771b(_0x4e0309 + _0x11dbad())
    // console.log(_0x422ded)

    // token生成:'_0x4e0309 = _0x4c771b(_0x4e0309 + _0x3fedba + _0x589b78 + _0x422ded) + ':' + (parseInt(_0x4e0309) + 0x493e0) || '''
    // _0x4e0309:时间戳
    // _0x3fedba：参数中 captchaId 固定值 "qDG21VMg9qS5Rcok4cfpnHGnpf5LhcAv"
    // _0x589b78：固定值 'slide'
    // _0x422ded: 前面生成captchaKey值
    // _0x4c771b() 和之前captchaKey值 生成方法一样

    // token 参数生成
    _0x4e0309 = _0x4c771b(_0x4e0309 + _0x3fedba + _0x589b78 + _0x422ded) + ':' + (parseInt(_0x4e0309) + 0x493e0) || ''

    // iv参数生成
    // _0x4c771b(_0x3fedba + _0x589b78 + Date[_0x5876dc(0x3d5)]() + _0x11dbad())
    // _0x3fedba：参数captchaId
    // _0x589b78：参数version
    // Date[_0x5876dc(0x3d5)]()：获取时间戳
    // _0x11dbad() 随机生成参数
    // _0x4c771b()：MD5加密
    iv = _0x4c771b(_0x3fedba + _0x589b78 + Date['now']() + _0x11dbad())
    data = {
        'callback': 'cx_captcha_function',
        'captchaId': _0x3fedba,
        'type': _0x589b78,
        'version': "1.1.20",
        'captchaKey': _0x422ded,
        'token': _0x4e0309,
        'referer': "https://authserver.whsw.cn/cas/login?service=https%3A%2F%2Fauthserver.whsw.cn%2Flogin",
        // 'iv': _0x4015b8[_0x5876dc(0x33f)]
        'iv': iv,
        // '_': _0x4e0309
        // '_': 1763400659382
    }
    // console.log(data)
    return data
}