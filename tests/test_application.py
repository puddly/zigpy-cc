# flake8: noqa: E501
import asyncio
from unittest import mock

import pytest
from zigpy.types import EUI64, Group, BroadcastAddress
import zigpy.zdo.types as zdo_t
from zigpy.zcl.clusters.general import Groups

from zigpy_cc import types as t
from zigpy_cc.api import API
import zigpy_cc.config as config
import zigpy_cc.zigbee.application as application
from zigpy_cc.zpi_object import ZpiObject

APP_CONFIG = {
    config.CONF_DEVICE: {
        config.CONF_DEVICE_PATH: "/dev/null",
        config.CONF_DEVICE_BAUDRATE: 115200,
    },
    config.CONF_DATABASE: None,
}


@pytest.fixture
def app():
    app = application.ControllerApplication(APP_CONFIG)
    app._api = API(APP_CONFIG[config.CONF_DEVICE])
    app._api.set_application(app)
    app._semaphore = asyncio.Semaphore()
    return app


@pytest.fixture
def ieee():
    return EUI64.deserialize(b"\x00\x01\x02\x03\x04\x05\x06\x07")[0]


@pytest.fixture
def nwk():
    return t.uint16_t(0x0100)


@pytest.fixture
def addr_ieee(ieee):
    addr = t.Address()
    addr.address_mode = t.ADDRESS_MODE.IEEE
    addr.address = ieee
    return addr


@pytest.fixture
def addr_nwk(nwk):
    addr = t.Address()
    addr.address_mode = t.ADDRESS_MODE.NWK
    addr.address = nwk
    return addr


@pytest.fixture
def addr_nwk_and_ieee(nwk, ieee):
    addr = t.Address()
    addr.address_mode = t.ADDRESS_MODE.NWK_AND_IEEE
    addr.address = nwk
    addr.ieee = ieee
    return addr


def test_join(app):
    payload = {"nwkaddr": 27441, "extaddr": "0x07a3c302008d1500", "parentaddr": 0}
    obj = ZpiObject(2, 5, "tcDeviceInd", 202, payload, [])
    app.handle_znp(obj)

    print(app.devices)

    payload = {
        "groupid": 0,
        "clusterid": 6,
        "srcaddr": 27441,
        "srcendpoint": 1,
        "dstendpoint": 1,
        "wasbroadcast": 0,
        "linkquality": 136,
        "securityuse": 0,
        "timestamp": 15458350,
        "transseqnumber": 0,
        "len": 7,
        "data": bytearray(b"\x18\x0c\n\x00\x00\x10\x00"),
    }
    obj = ZpiObject(2, 4, "incomingMsg", 129, payload, [])
    app.handle_znp(obj)


"""
DEBUG:zigpy_cc.api:--> AREQ ZDO tcDeviceInd {'nwkaddr': 19542, 'extaddr': '0x07a3c302008d1500', 'parentaddr': 0}
INFO:zigpy_cc.zigbee.application:New device joined: 0x4c56, 32:30:33:63:33:61:37:30
INFO:zigpy.application:Device 0x4c56 (32:30:33:63:33:61:37:30) joined the network

INFO:zigpy.device:[0x4c56] Requesting 'Node Descriptor'
Tries remaining: 2
DEBUG:zigpy.device:[0x4c56] Extending timeout for 0x01 request
DEBUG:zigpy_cc.zigbee.application:Sending Zigbee request with tsn 1 under 2 request id, data: b'01564c'
profile 0
cluster ZDOCmd.Node_Desc_req
src_ep 0
dst_ep 0
WARNING:zigpy.device:[0x4c56] Requesting Node Descriptor failed: 'destination'

INFO:zigpy.device:[0x4c56] Discovering endpoints
Tries remaining: 3
DEBUG:zigpy.device:[0x4c56] Extending timeout for 0x03 request
DEBUG:zigpy_cc.zigbee.application:Sending Zigbee request with tsn 3 under 4 request id, data: b'03564c'
profile 0
cluster ZDOCmd.Active_EP_req
src_ep 0
dst_ep 0

INFO:zigpy.device:[0xd04a] Requesting 'Node Descriptor'
Tries remaining: 2
DEBUG:zigpy.device:[0xd04a] Extending timeout for 0x05 request
DEBUG:zigpy_cc.zigbee.application:Sending Zigbee request with tsn 5 under 6 request id, data: b'054ad0'
WARNING:zigpy.device:[0xd04a] Requesting Node Descriptor failed: 'API' object has no attribute 'aps_data_request'
INFO:zigpy.device:[0xd04a] Discovering endpoints
Tries remaining: 3
DEBUG:zigpy.device:[0xd04a] Extending timeout for 0x07 request
DEBUG:zigpy_cc.zigbee.application:Sending Zigbee request with tsn 7 under 8 request id, data: b'074ad0'
ERROR:zigpy.device:Failed ZDO request during device initialization: 'API' object has no attribute 'aps_data_request'

INFO:zigpy.device:[0xc00c] Requesting 'Node Descriptor'
Tries remaining: 2
DEBUG:zigpy.device:[0xc00c] Extending timeout for 0x09 request
DEBUG:zigpy_cc.zigbee.application:Sending Zigbee request with tsn 9 under 10 request id, data: b'090cc0'
WARNING:zigpy.device:[0xc00c] Requesting Node Descriptor failed: 'API' object has no attribute 'aps_data_request'
INFO:zigpy.device:[0xc00c] Discovering endpoints
Tries remaining: 3
DEBUG:zigpy.device:[0xc00c] Extending timeout for 0x0b request
DEBUG:zigpy_cc.zigbee.application:Sending Zigbee request with tsn 11 under 12 request id, data: b'0b0cc0'
ERROR:zigpy.device:Failed ZDO request during device initialization: 'API' object has no attribute 'aps_data_request'
"""


async def device_annce(app: application.ControllerApplication):
    # payload = {'nwkaddr': 27441, 'extaddr': '0x07a3c302008d1500', 'parentaddr': 0}
    # obj = ZpiObject(2, 5, 'tcDeviceInd', 202, payload, [])

    payload = {
        "srcaddr": 53322,
        "nwkaddr": 53322,
        "ieeeaddr": 0x41E54B02008D1500 .to_bytes(8, "little"),
        "capabilities": 132,
    }
    obj = ZpiObject(2, 5, "endDeviceAnnceInd", 193, payload, [])

    app.handle_znp(obj)


@pytest.mark.asyncio
async def test_request(app: application.ControllerApplication):
    await device_annce(app)
    device = app.get_device(nwk=53322)

    fut = asyncio.Future()
    fut.set_result(None)
    app._api.request_raw = mock.MagicMock(return_value=fut)

    res = await app.request(
        device, 0, zdo_t.ZDOCmd.Node_Desc_req, 0, 0, 1, b"\x01\xa2\x2e"
    )

    assert len(app._api._waiters) == 1
    assert (
        "SREQ ZDO nodeDescReq tsn: 1 {'dstaddr': 0xd04a, 'nwkaddrofinterest': 0x2ea2}"
        == str(app._api.request_raw.call_args[0][0])
    )
    assert res == (0, "message send success")


@pytest.mark.asyncio
async def test_mrequest(app: application.ControllerApplication):
    fut = asyncio.Future()
    fut.set_result(None)
    app._api.request_raw = mock.MagicMock(return_value=fut)

    # multicast (0x0002, 260, 6, 1, 39, b"\x01'\x00", 0, 3)
    res = await app.mrequest(Group(2), 260, Groups.cluster_id, 1, 39, b"\x01'\x00")

    assert 1 == len(app._api._waiters)
    assert (
        "SREQ AF dataRequestExt tsn: 39 {'dstaddrmode': <AddressMode.ADDR_GROUP: 1>, "
        "'dstaddr': 0x0002, 'destendpoint': 255, 'dstpanid': 0, "
        "'srcendpoint': 1, 'clusterid': 4, 'transid': 39, 'options': 0, 'radius': 30, 'len': 3, "
        "'data': b\"\\x01'\\x00\"}" == str(app._api.request_raw.call_args[0][0])
    )
    assert (0, "message send success") == res


@pytest.mark.asyncio
async def test_broadcast(app: application.ControllerApplication):
    fut = asyncio.Future()
    fut.set_result(None)
    app._api.request_raw = mock.MagicMock(return_value=fut)

    # broadcast (0, 54, 0, 0, 0, 0, 45, b'-<\x00', <BroadcastAddress.ALL_ROUTERS_AND_COORDINATOR: 65532>)
    res = await app.broadcast(
        0, 54, 0, 0, 0, 0, 45, b"-<\x00", BroadcastAddress.ALL_ROUTERS_AND_COORDINATOR
    )

    assert 0 == len(app._api._waiters)
    assert (
        "SREQ ZDO mgmtPermitJoinReq tsn: 45 {'addrmode': <AddressMode.ADDR_BROADCAST: 15>, "
        "'dstaddr': 0xfffc, 'duration': 60, 'tcsignificance': 0}"
        == str(app._api.request_raw.call_args[0][0])
    )
    assert (0, "broadcast send success") == res


"""
zigpy_cc.api DEBUG <-- SREQ ZDO nodeDescReq {'dstaddr': 53322, 'nwkaddrofinterest': 0}
zigpy_cc.api DEBUG --> SRSP ZDO nodeDescReq {'status': 0}
zigpy_cc.api DEBUG --> AREQ ZDO nodeDescRsp {'srcaddr': 53322, 'status': 128, 'nwkaddr': 0, 
    'logicaltype_cmplxdescavai_userdescavai': 0, 'apsflags_freqband': 0, 'maccapflags': 0, 'manufacturercode': 0, 
    'maxbuffersize': 0, 'maxintransfersize': 0, 'servermask': 0, 'maxouttransfersize': 0, 'descriptorcap': 0}
"""


@pytest.mark.asyncio
async def test_get_node_descriptor(app: application.ControllerApplication):
    await device_annce(app)
    device = app.get_device(nwk=53322)

    fut = asyncio.Future()
    fut.set_result([0, "message send success"])
    app._api.request_raw = mock.MagicMock(return_value=fut)

    payload = {
        "srcaddr": 53322,
        "status": 0,
        "nwkaddr": 0,
        "logicaltype_cmplxdescavai_userdescavai": 0,
        "apsflags_freqband": 0,
        "maccapflags": 0,
        "manufacturercode": 1234,
        "maxbuffersize": 0,
        "maxintransfersize": 0,
        "servermask": 0,
        "maxouttransfersize": 0,
        "descriptorcap": 0,
    }
    obj = ZpiObject.from_command(5, "nodeDescRsp", payload)
    frame = obj.to_unpi_frame()

    async def nested():
        await asyncio.sleep(0)
        app._api.data_received(frame)

    await asyncio.wait([device.get_node_descriptor(), nested()], timeout=0.2)

    assert isinstance(device.node_desc, zdo_t.NodeDescriptor)
    assert 1234 == device.node_desc.manufacturer_code


@pytest.mark.asyncio
async def test_read_attributes(app: application.ControllerApplication):
    await device_annce(app)
    device = app.get_device(nwk=53322)

    # res = await app.request(device, 260, 0, 1, 1, 1, b'\x00\x0b\x00\x04\x00\x05\x00')
    #
    # assert res == []


# def _test_rx(app, addr_ieee, addr_nwk, device, data):
#     app.get_device = mock.MagicMock(return_value=device)
#     app.devices = (EUI64(addr_ieee.address),)
#
#     app.handle_rx(
#         addr_nwk,
#         mock.sentinel.src_ep,
#         mock.sentinel.dst_ep,
#         mock.sentinel.profile_id,
#         mock.sentinel.cluster_id,
#         data,
#         mock.sentinel.lqi,
#         mock.sentinel.rssi,
#     )
#
#
# def test_znp(app, addr_ieee, addr_nwk):
#     device = mock.MagicMock()
#     app.handle_message = mock.MagicMock()
#     _test_rx(app, addr_ieee, addr_nwk, device, mock.sentinel.args)
#     assert app.handle_message.call_count == 1
#     assert app.handle_message.call_args == (
#         (
#             device,
#             mock.sentinel.profile_id,
#             mock.sentinel.cluster_id,
#             mock.sentinel.src_ep,
#             mock.sentinel.dst_ep,
#             mock.sentinel.args,
#         ),
#     )
#
#
# def test_rx_ieee(app, addr_ieee, addr_nwk):
#     device = mock.MagicMock()
#     app.handle_message = mock.MagicMock()
#     _test_rx(app, addr_ieee, addr_ieee, device, mock.sentinel.args)
#     assert app.handle_message.call_count == 1
#     assert app.handle_message.call_args == (
#         (
#             device,
#             mock.sentinel.profile_id,
#             mock.sentinel.cluster_id,
#             mock.sentinel.src_ep,
#             mock.sentinel.dst_ep,
#             mock.sentinel.args,
#         ),
#     )
#
#
# def test_rx_nwk_ieee(app, addr_ieee, addr_nwk_and_ieee):
#     device = mock.MagicMock()
#     app.handle_message = mock.MagicMock()
#     _test_rx(app, addr_ieee, addr_nwk_and_ieee, device, mock.sentinel.args)
#     assert app.handle_message.call_count == 1
#     assert app.handle_message.call_args == (
#         (
#             device,
#             mock.sentinel.profile_id,
#             mock.sentinel.cluster_id,
#             mock.sentinel.src_ep,
#             mock.sentinel.dst_ep,
#             mock.sentinel.args,
#         ),
#     )
#
#
# def test_rx_wrong_addr_mode(app, addr_ieee, addr_nwk, caplog):
#     device = mock.MagicMock()
#     app.handle_message = mock.MagicMock()
#     app.get_device = mock.MagicMock(return_value=device)
#
#     app.devices = (EUI64(addr_ieee.address),)
#
#     with pytest.raises(Exception):  # TODO: don't use broad exceptions
#         addr_nwk.address_mode = 0x22
#         app.handle_rx(
#             addr_nwk,
#             mock.sentinel.src_ep,
#             mock.sentinel.dst_ep,
#             mock.sentinel.profile_id,
#             mock.sentinel.cluster_id,
#             b"",
#             mock.sentinel.lqi,
#             mock.sentinel.rssi,
#         )
#
#     assert app.handle_message.call_count == 0
#
#
# def test_rx_unknown_device(app, addr_ieee, addr_nwk, caplog):
#     app.handle_message = mock.MagicMock()
#
#     caplog.set_level(logging.DEBUG)
#     app.handle_rx(
#         addr_nwk,
#         mock.sentinel.src_ep,
#         mock.sentinel.dst_ep,
#         mock.sentinel.profile_id,
#         mock.sentinel.cluster_id,
#         b"",
#         mock.sentinel.lqi,
#         mock.sentinel.rssi,
#     )
#
#     assert "Received frame from unknown device" in caplog.text
#     assert app.handle_message.call_count == 0
#
#
# # @pytest.mark.asyncio
# # async def test_form_network(app):
# #     app._api.change_network_state = mock.MagicMock(
# #         side_effect=asyncio.coroutine(mock.MagicMock())
# #     )
# #     app._api.device_state = mock.MagicMock(
# #         side_effect=asyncio.coroutine(mock.MagicMock())
# #     )
# #
# #     app._api.network_state = 2
# #     await app.form_network()
# #     assert app._api.device_state.call_count == 0
# #
# #     app._api.network_state = 0
# #     application.CHANGE_NETWORK_WAIT = 0.001
# #     with pytest.raises(Exception):
# #         await app.form_network()
# #     assert app._api.device_state.call_count == 10
#
#
# @pytest.mark.parametrize(
#     "protocol_ver, watchdog_cc", [(0x0107, False), (0x0108, True), (0x010B, True)]
# )
# @pytest.mark.asyncio
# async def test_startup(protocol_ver, watchdog_cc, app, monkeypatch, version=0):
#     async def _version():
#         app._api._proto_ver = protocol_ver
#         return [version]
#
#     app._reset_watchdog = mock.MagicMock(
#         side_effect=asyncio.coroutine(mock.MagicMock())
#     )
#     app.form_network = mock.MagicMock(side_effect=asyncio.coroutine(mock.MagicMock()))
#     app._api._command = mock.MagicMock(side_effect=asyncio.coroutine(mock.MagicMock()))
#     app._api.read_parameter = mock.MagicMock(
#         side_effect=asyncio.coroutine(mock.MagicMock(return_value=[[0]]))
#     )
#     app._api.version = mock.MagicMock(side_effect=_version)
#     app._api.write_parameter = mock.MagicMock(
#         side_effect=asyncio.coroutine(mock.MagicMock())
#     )
#
#     new_mock = mock.MagicMock(side_effect=asyncio.coroutine(mock.MagicMock()))
#     monkeypatch.setattr(application.ConBeeDevice, "new", new_mock)
#     await app.startup(auto_form=False)
#     assert app.form_network.call_count == 0
#     assert app._reset_watchdog.call_count == watchdog_cc
#     await app.startup(auto_form=True)
#     assert app.form_network.call_count == 1
#
#
# @pytest.mark.asyncio
# async def test_permit(app, nwk):
#     app._api.write_parameter = mock.MagicMock(
#         side_effect=asyncio.coroutine(mock.MagicMock())
#     )
#     time_s = 30
#     await app.permit_ncp(time_s)
#     assert app._api.write_parameter.call_count == 1
#     assert app._api.write_parameter.call_args_list[0][0][1] == time_s
#
#
# async def _test_request(app, send_success=True, aps_data_error=False, **kwargs):
#     seq = 123
#
#     async def req_mock(req_id, dst_addr_ep, profile, cluster, src_ep, data):
#         if aps_data_error:
#             raise zigpy_cc.exception.CommandError(1, "Command Error")
#         if send_success:
#             app._pending[req_id].result.set_result(0)
#         else:
#             app._pending[req_id].result.set_result(1)
#
#     app._api.aps_data_request = mock.MagicMock(side_effect=req_mock)
#     device = zigpy.device.Device(app, mock.sentinel.ieee, 0x1122)
#     app.get_device = mock.MagicMock(return_value=device)
#
#     return await app.request(device, 0x0260, 1, 2, 3, seq, b"\x01\x02\x03", **kwargs)
#
#
# @pytest.mark.asyncio
# async def test_request_send_success(app):
#     req_id = mock.sentinel.req_id
#     app.get_sequence = mock.MagicMock(return_value=req_id)
#     r = await _test_request(app, True)
#     assert r[0] == 0
#
#     r = await _test_request(app, True, use_ieee=True)
#     assert r[0] == 0
#
#
# @pytest.mark.asyncio
# async def test_request_send_fail(app):
#     req_id = mock.sentinel.req_id
#     app.get_sequence = mock.MagicMock(return_value=req_id)
#     r = await _test_request(app, False)
#     assert r[0] != 0
#
#
# @pytest.mark.asyncio
# async def test_request_send_aps_data_error(app):
#     req_id = mock.sentinel.req_id
#     app.get_sequence = mock.MagicMock(return_value=req_id)
#     r = await _test_request(app, False, aps_data_error=True)
#     assert r[0] != 0
#
#
# async def _test_broadcast(app, send_success=True, aps_data_error=False, **kwargs):
#     seq = mock.sentinel.req_id
#
#     async def req_mock(req_id, dst_addr_ep, profile, cluster, src_ep, data):
#         if aps_data_error:
#             raise zigpy_cc.exception.CommandError(1, "Command Error")
#         if send_success:
#             app._pending[req_id].result.set_result(0)
#         else:
#             app._pending[req_id].result.set_result(1)
#
#     app._api.aps_data_request = mock.MagicMock(side_effect=req_mock)
#     app.get_device = mock.MagicMock(spec_set=zigpy.device.Device)
#
#     r = await app.broadcast(
#         mock.sentinel.profile,
#         mock.sentinel.cluster,
#         2,
#         mock.sentinel.dst_ep,
#         mock.sentinel.grp_id,
#         mock.sentinel.radius,
#         seq,
#         b"\x01\x02\x03",
#         **kwargs
#     )
#     assert app._api.aps_data_request.call_count == 1
#     assert app._api.aps_data_request.call_args[0][0] is seq
#     assert app._api.aps_data_request.call_args[0][2] is mock.sentinel.profile
#     assert app._api.aps_data_request.call_args[0][3] is mock.sentinel.cluster
#     assert app._api.aps_data_request.call_args[0][5] == b"\x01\x02\x03"
#     return r
#
#
# @pytest.mark.asyncio
# async def test_broadcast_send_success(app):
#     req_id = mock.sentinel.req_id
#     app.get_sequence = mock.MagicMock(return_value=req_id)
#     r = await _test_broadcast(app, True)
#     assert r[0] == 0
#
#
# @pytest.mark.asyncio
# async def test_broadcast_send_fail(app):
#     req_id = mock.sentinel.req_id
#     app.get_sequence = mock.MagicMock(return_value=req_id)
#     r = await _test_broadcast(app, False)
#     assert r[0] != 0
#
#
# @pytest.mark.asyncio
# async def test_broadcast_send_aps_data_error(app):
#     req_id = mock.sentinel.req_id
#     app.get_sequence = mock.MagicMock(return_value=req_id)
#     r = await _test_broadcast(app, False, aps_data_error=True)
#     assert r[0] != 0
#
#
# def _handle_reply(app, tsn):
#     app.handle_message = mock.MagicMock()
#     return app._handle_reply(
#         mock.sentinel.device,
#         mock.sentinel.profile,
#         mock.sentinel.cluster,
#         mock.sentinel.src_ep,
#         mock.sentinel.dst_ep,
#         tsn,
#         mock.sentinel.command_id,
#         mock.sentinel.args,
#     )
#
#
# @pytest.mark.asyncio
# async def test_shutdown(app):
#     app._api.close = mock.MagicMock()
#     await app.shutdown()
#     assert app._api.close.call_count == 1
#
#
# def test_rx_device_annce(app, addr_ieee, addr_nwk):
#     dst_ep = 0
#     cluster_id = zdo_t.ZDOCmd.Device_annce
#     device = mock.MagicMock()
#     device.status = zigpy.device.Status.NEW
#     app.get_device = mock.MagicMock(return_value=device)
#
#     app.handle_join = mock.MagicMock()
#     app._handle_reply = mock.MagicMock()
#     app.handle_message = mock.MagicMock()
#
#     data = t.uint8_t(0xAA).serialize()
#     data += addr_nwk.address.serialize()
#     data += addr_ieee.address.serialize()
#     data += t.uint8_t(0x8E).serialize()
#
#     app.handle_rx(
#         addr_nwk,
#         mock.sentinel.src_ep,
#         dst_ep,
#         mock.sentinel.profile_id,
#         cluster_id,
#         data,
#         mock.sentinel.lqi,
#         mock.sentinel.rssi,
#     )
#
#     assert app.handle_message.call_count == 1
#     assert app.handle_join.call_count == 1
#     assert app.handle_join.call_args[0][0] == addr_nwk.address
#     assert app.handle_join.call_args[0][1] == addr_ieee.address
#     assert app.handle_join.call_args[0][2] == 0
#
#
# @pytest.mark.asyncio
# async def test_conbee_dev_add_to_group(app, nwk):
#     group = mock.MagicMock()
#     app._groups = mock.MagicMock()
#     app._groups.add_group.return_value = group
#
#     conbee = application.ConBeeDevice(app, mock.sentinel.ieee, nwk)
#     conbee.endpoints = {
#         0: mock.sentinel.zdo,
#         1: mock.sentinel.ep1,
#         2: mock.sentinel.ep2,
#     }
#
#     await conbee.add_to_group(mock.sentinel.grp_id, mock.sentinel.grp_name)
#     assert group.add_member.call_count == 2
#
#     assert app.groups.add_group.call_count == 1
#     assert app.groups.add_group.call_args[0][0] is mock.sentinel.grp_id
#     assert app.groups.add_group.call_args[0][1] is mock.sentinel.grp_name
#
#
# @pytest.mark.asyncio
# async def test_conbee_dev_remove_from_group(app, nwk):
#     group = mock.MagicMock()
#     app.groups[mock.sentinel.grp_id] = group
#     conbee = application.ConBeeDevice(app, mock.sentinel.ieee, nwk)
#     conbee.endpoints = {
#         0: mock.sentinel.zdo,
#         1: mock.sentinel.ep1,
#         2: mock.sentinel.ep2,
#     }
#
#     await conbee.remove_from_group(mock.sentinel.grp_id)
#     assert group.remove_member.call_count == 2
#
#
# def test_conbee_props(nwk):
#     conbee = application.ConBeeDevice(app, mock.sentinel.ieee, nwk)
#     assert conbee.manufacturer is not None
#     assert conbee.model is not None
#
#
# @pytest.mark.asyncio
# async def test_conbee_new(app, nwk, monkeypatch):
#     mock_init = mock.MagicMock(side_effect=asyncio.coroutine(mock.MagicMock()))
#     monkeypatch.setattr(zigpy.device.Device, "_initialize", mock_init)
#
#     conbee = await application.ConBeeDevice.new(app, mock.sentinel.ieee, nwk)
#     assert isinstance(conbee, application.ConBeeDevice)
#     assert mock_init.call_count == 1
#     mock_init.reset_mock()
#
#     mock_dev = mock.MagicMock()
#     mock_dev.endpoints = {
#         0: mock.MagicMock(),
#         1: mock.MagicMock(),
#         22: mock.MagicMock(),
#     }
#     app.devices[mock.sentinel.ieee] = mock_dev
#     conbee = await application.ConBeeDevice.new(app, mock.sentinel.ieee, nwk)
#     assert isinstance(conbee, application.ConBeeDevice)
#     assert mock_init.call_count == 0
#
#
# def test_tx_confirm_success(app):
#     tsn = 123
#     req = app._pending[tsn] = mock.MagicMock()
#     app.handle_tx_confirm(tsn, mock.sentinel.status)
#     assert req.result.set_result.call_count == 1
#     assert req.result.set_result.call_args[0][0] is mock.sentinel.status
#
#
# def test_tx_confirm_dup(app, caplog):
#     caplog.set_level(logging.DEBUG)
#     tsn = 123
#     req = app._pending[tsn] = mock.MagicMock()
#     req.result.set_result.side_effect = asyncio.InvalidStateError
#     app.handle_tx_confirm(tsn, mock.sentinel.status)
#     assert req.result.set_result.call_count == 1
#     assert req.result.set_result.call_args[0][0] is mock.sentinel.status
#     assert any(r.levelname == "DEBUG" for r in caplog.records)
#     assert "probably duplicate response" in caplog.text
#
#
# def test_tx_confirm_unexpcted(app, caplog):
#     app.handle_tx_confirm(123, 0x00)
#     assert any(r.levelname == "WARNING" for r in caplog.records)
#     assert "Unexpected transmit confirm for request id" in caplog.text
#
#
# async def _test_mrequest(app, send_success=True, aps_data_error=False, **kwargs):
#     seq = 123
#     req_id = mock.sentinel.req_id
#     app.get_sequence = mock.MagicMock(return_value=req_id)
#
#     async def req_mock(req_id, dst_addr_ep, profile, cluster, src_ep, data):
#         if aps_data_error:
#             raise zigpy_cc.exception.CommandError(1, "Command Error")
#         if send_success:
#             app._pending[req_id].result.set_result(0)
#         else:
#             app._pending[req_id].result.set_result(1)
#
#     app._api.aps_data_request = mock.MagicMock(side_effect=req_mock)
#     device = zigpy.device.Device(app, mock.sentinel.ieee, 0x1122)
#     app.get_device = mock.MagicMock(return_value=device)
#
#     return await app.mrequest(0x55AA, 0x0260, 1, 2, seq, b"\x01\x02\x03", **kwargs)
#
#
# @pytest.mark.asyncio
# async def test_mrequest_send_success(app):
#     r = await _test_mrequest(app, True)
#     assert r[0] == 0
#
#
# @pytest.mark.asyncio
# async def test_mrequest_send_fail(app):
#     r = await _test_mrequest(app, False)
#     assert r[0] != 0
#
#
# @pytest.mark.asyncio
# async def test_mrequest_send_aps_data_error(app):
#     r = await _test_mrequest(app, False, aps_data_error=True)
#     assert r[0] != 0
