# Feishu API Reference for Payroll Approval Migration

> API guide for migrating Payroll2DingTalk from DingTalk to Feishu.
> Covers authentication, user lookup, file upload, approval definition, and instance creation.
---
## 1. Authentication

| Item | Value |
|------|-------|
| URL | `POST /open-apis/auth/v3/tenant_access_token/internal` |
| Method | POST |
| Token | None (this endpoint issues the token) |
### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| app_id | string | Yes | Feishu application ID |
| app_secret | string | Yes | Feishu application secret |

```json
{"app_id": "cli_xxx", "app_secret": "xxx"}
```
### Response

| Field | Type | Description |
|-------|------|-------------|
| tenant_access_token | string | Bearer token for subsequent calls |
| expire | int | TTL in seconds (default 7200) |
### Python SDK Example

```python
from lark_oapi import Client

client = Client.builder() \
    .app_id("cli_xxx") \
    .app_secret("xxx") \
    .build()
# SDK auto-manages tenant_access_token internally.
```
### Pitfalls

- Token expires in 2 hours. Refresh 5 minutes early.
- SDK `Client` caches the token. Do NOT share one client across threads without locks if constructing manually.
---
## 2. User Query
### 2.1 Batch Get User ID by Mobile

| Item | Value |
|------|-------|
| URL | `POST /open-apis/contact/v3/users/batch_get_id?user_id_type=open_id` |
| Method | POST |
| Token | tenant_access_token |
#### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| mobiles | string[] | Yes | List of mobile numbers |
| include_resigned | bool | No | Include resigned users |

```json
{"mobiles": ["13800138000"]}
```
#### Response

```json
{"code": 0, "data": {"user_list": [{"mobile": "13800138000", "user_id": "ou_xxx"}]}}
```
#### Python SDK Example

```python
from lark_oapi.api.contact.v3 import BatchGetIdUserRequest, BatchGetIdUserRequestBody

body = BatchGetIdUserRequestBody.builder().mobiles(["13800138000"]).build()
req = BatchGetIdUserRequest.builder().user_id_type("open_id").request_body(body).build()
resp = client.contact.v3.user.batch_get_id(req)
open_id = resp.data.user_list[0].user_id
```
### 2.2 Get User Detail

| Item | Value |
|------|-------|
| URL | `GET /open-apis/contact/v3/users/:user_id` |
| Method | GET |
| Token | tenant_access_token or user_access_token |
#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | path | Yes | Target user ID |
| user_id_type | query | Yes | `open_id` / `user_id` / `union_id` |
| department_id_type | query | No | `department_id` / `open_department_id` |
#### Response

```json
{"code": 0, "data": {"user": {"user_id": "ou_xxx", "name": "Zhang San", "department_ids": ["od-xxx"]}}}
```
#### Python SDK Example

```python
from lark_oapi.api.contact.v3 import GetUserRequest

req = GetUserRequest.builder() \
    .user_id("ou_xxx").user_id_type("open_id") \
    .department_id_type("open_department_id").build()
resp = client.contact.v3.user.get(req)
```
### Pitfalls

- `batch_get_id` returns `user_id` field even when `user_id_type=open_id`. The field name is always `user_id`, but the value is the requested type.
- Missing mobiles are omitted from `user_list` instead of returning an error. Always check list length.
- `department_ids` may be empty. Feishu does NOT support root department (`0`) in approval creation.
---
## 3. Approval File Upload

| Item | Value |
|------|-------|
| URL | `POST /approval/openapi/v2/file/upload` |
| Method | POST |
| Content-Type | `multipart/form-data` |
| Token | tenant_access_token |
### Request Parameters (multipart)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Original file name |
| type | string | Yes | `attachment` or `image` |
| content | binary | Yes | Raw file bytes |
### Response

```json
{"code": 0, "data": {"code": "file_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}}
```

`data.code` is a UUID string used as `file_code` in `attachmentV2` widgets.
### Python SDK Example (Native BaseRequest)

The lark-oapi SDK does **not** provide a typed wrapper for this endpoint. Use `BaseRequest` with `MultipartEncoder`.

```python
from requests_toolbelt import MultipartEncoder
from lark_oapi import BaseRequest

multi = MultipartEncoder(fields=[
    ("name", "salary.xlsx"),
    ("type", "attachment"),
    ("content", ("salary.xlsx", file_bytes, "application/octet-stream")),
])
req = BaseRequest()
req.http_method = "POST"
req.uri = "/open-apis/approval/openapi/v2/file/upload"
req.body = multi
req.headers = {"Content-Type": multi.content_type}
resp = client.raw_request(req)
file_code = resp.data["code"]
```
### Pitfalls

- **SDK has NO typed wrapper for file/upload**. Raw `BaseRequest` is mandatory.
- Must be `multipart/form-data`, not JSON.
- `type` must be exactly `attachment` (not `file`).
- Max file size typically 200 MB (tenant-dependent).
---
## 4. Approval Definition Query

| Item | Value |
|------|-------|
| URL | `GET /open-apis/approval/v4/approvals/:approval_code` |
| Method | GET |
| Token | tenant_access_token |
### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| approval_code | path | Yes | Template code from Feishu admin console |
| user_id_type | query | No | `open_id` / `user_id` / `union_id` |
| locale | query | No | `zh-CN` / `en-US` / `ja-JP` |
### Response

```json
{
  "code": 0,
  "data": {
    "approval_code": "xxx",
    "approval_name": "Salary Approval",
    "form": [
      {"id": "widget1", "type": "input", "name": "Title", "required": true},
      {"id": "widget2", "type": "attachmentV2", "name": "Attachments", "required": true},
      {"id": "widget3", "type": "fieldList", "name": "Summary Table", "required": true},
      {"id": "widget4", "type": "textarea", "name": "Remarks", "required": false}
    ]
  }
}
```
### Python SDK Example

```python
from lark_oapi.api.approval.v4 import GetApprovalRequest

req = GetApprovalRequest.builder() \
    .approval_code("your_approval_code") \
    .user_id_type("open_id").locale("zh-CN").build()
resp = client.approval.v4.approval.get(req)
widgets = resp.data.form
```
### Pitfalls

- **Widget IDs are dynamic** (`widget1`, `widget2`, etc.). Call this API to map config labels to widget IDs before creating instances.
- `required` is only metadata. The create-instance API does NOT enforce it. Validate fields yourself.
---
## 5. Create Approval Instance

| Item | Value |
|------|-------|
| URL | `POST /open-apis/approval/v4/instances` |
| Method | POST |
| Token | tenant_access_token |
### Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| approval_code | string | Yes | Approval template code |
| open_id | string | Yes* | Initiator open_id (or user_id) |
| department_id | string | No | Department ID (root unsupported) |
| form | string | Yes | **JSON-serialized string** of form array |
| locale | string | Yes | `zh-CN` |
| uuid | string | Yes | Client UUID for idempotency |
| title | string | No | Instance title |

```json
{
  "approval_code": "xxx",
  "open_id": "ou_xxx",
  "form": "[{\"id\":\"widget1\",\"type\":\"input\",\"value\":\"Title\"}]",
  "locale": "zh-CN",
  "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

`form` is a **string**, not an array.
### Response

```json
{"code": 0, "data": {"instance_code": "xxx"}}
```
### Python SDK Example

```python
import json
from lark_oapi.api.approval.v4 import CreateInstanceRequest, InstanceCreate

form_array = [
    {"id": "widget1", "type": "input", "value": "Jan Salary"},
    {"id": "widget2", "type": "attachmentV2", "value": ["file_code_xxx"]},
    {"id": "widget3", "type": "fieldList", "value": [[
        {"id": "sub1", "type": "input", "value": "Row1Col1"},
        {"id": "sub2", "type": "number", "value": "1000.00"}
    ]]},
]

body = InstanceCreate.builder() \
    .approval_code("xxx").open_id("ou_xxx") \
    .form(json.dumps(form_array, ensure_ascii=False)) \
    .locale("zh-CN").uuid("a1b2c3d4-...").build()
req = CreateInstanceRequest.builder().request_body(body).build()
resp = client.approval.v4.instance.create(req)
instance_code = resp.data.instance_code
```
### Pitfalls

- **form MUST be a JSON string**, not a Python list. Use `json.dumps()`.
- **Number widget value must be a string** (`"123.45"`), not float/int.
- **fieldList value is a 2-D array**: `[[row1_cols], [row2_cols]]`.
- **attachmentV2 value is a list of file_code strings** from the upload API.
- **uuid is idempotent**. Reuse returns error `60012`.
- **department_id does not support root department**.
- The API does NOT validate `required` fields.
---
## Appendix A: Form Control Types and Value Format

| Control | Value Type | Example | Notes |
|---------|------------|---------|-------|
| input | string | `"Title"` | Single-line text |
| textarea | string | `"Notes"` | Multi-line text |
| number | **string** | `"1234.56"` | Must be string, not numeric |
| money | object | `{"amount":"1000.00","currency":"CNY"}` | Both strings |
| attachmentV2 | string[] | `["file_code_1"]` | Upload files first |
| fieldList | 2-D array | `[[{"id":"a","type":"input","value":"v"}]]` | Outer = rows |
| radioV2 | string | `"option_id_1"` | Selected option ID |
| checkbox | string[] | `["opt_1","opt_2"]` | Selected option IDs |
| date | string | `"2024-01-15"` | ISO date |
| dateInterval | object | `{"start":"2024-01-01","end":"2024-01-31"}` | Date range |
---
## Appendix B: DingTalk to Feishu API Mapping

| # | DingTalk API | Feishu API | Notes |
|---|-------------|-----------|-------|
| 1 | `POST /v1.0/oauth2/accessToken` | `POST /auth/v3/tenant_access_token/internal` | Feishu unified single token |
| 2 | `GET /oapi.dingtalk.com/gettoken` | (n/a) | No old-style token in Feishu |
| 3 | `POST /topapi/v2/user/getbymobile` | `POST /contact/v3/users/batch_get_id` | Batch lookup by mobiles |
| 4 | `POST /topapi/v2/user/get` | `GET /contact/v3/users/:user_id` | Direct GET |
| 5 | `POST /workflow/processInstances/spaces/infos/query` | (n/a) | No space auth needed |
| 6 | `POST /storage/spaces/:spaceId/files/uploadInfos/query` | (n/a) | Feishu single-step upload |
| 7 | `PUT OSS` | (n/a) | Internal storage |
| 8 | `POST /storage/spaces/:spaceId/files/commit` | `POST /approval/openapi/v2/file/upload` | Single multipart call |
| 9 | `POST /v1.0/workflow/processInstances` | `POST /approval/v4/instances` | Feishu form is JSON string |
---
## Appendix C: SDK Method Signatures (lark-oapi v2_main)

```python
# C.1 BatchGetIdUserRequest
class BatchGetIdUserRequest(BaseRequest):
    user_id_type: Optional[str]
    request_body: Optional[BatchGetIdUserRequestBody]
# Builder: .user_id_type(str) .request_body(BatchGetIdUserRequestBody) .build()
# C.2 GetUserRequest
class GetUserRequest(BaseRequest):
    user_id_type: Optional[str]
    department_id_type: Optional[str]
    user_id: Optional[str]
# Builder: .user_id_type(str) .department_id_type(str) .user_id(str) .build()
# C.3 GetApprovalRequest
class GetApprovalRequest(BaseRequest):
    locale: Optional[str]
    with_admin_id: Optional[bool]
    user_id_type: Optional[str]
    with_option: Optional[bool]
    user_id: Optional[str]
    nested_mutable_group: Optional[bool]
    approval_code: Optional[str]
# Builder: .approval_code(str) .user_id_type(str) .locale(str) ... .build()
# C.4 CreateInstanceRequest
class CreateInstanceRequest(BaseRequest):
    request_body: Optional[InstanceCreate]
# Builder: .request_body(InstanceCreate) .build()
# InstanceCreate builder: .approval_code(str) .open_id(str) .form(str) .uuid(str) .locale(str) ...
```
---
## Appendix D: Feishu Permission Checklist

Apply these in the Feishu Open Platform under your app settings.

| Permission Code | Purpose | Required |
|----------------|---------|----------|
| `contact:user.id:readonly` | Lookup user ID by mobile | Yes |
| `contact:user.base:readonly` | Read basic user info | Yes |
| `approval:approval` | Create approval instances | Yes |
| `approval:approval:readonly` | Query definitions and upload files | Yes |
| `contact:user.employee_id:readonly` | Get user_id detail | No |
| `drive:drive:readonly` | Read Drive files | No |
---
## Appendix E: Common Error Codes

| Code | Meaning | Resolution |
|------|---------|------------|
| 0 | Success | — |
| 60012 | Duplicate instance (uuid reused) | Generate new uuid |
| 99991663 / 99991664 | Invalid / expired token | Refresh tenant_access_token |
| 100000 | Parameter error | Check body format |
| 40001 | Approval code not found | Verify in admin console |
| 40002 | User not found | Check open_id / user_id |
| 40003 | Department not found | Do not use root department |
| 40005 | Form format invalid | Ensure form is a JSON string |
