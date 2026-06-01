I'll create a short todo plan and then produce concise request/response shapes for each admin API.

Created 2 todos

Progress: Drafting the request/response formats now — delivering concise API examples below.

Auth (for all endpoints)

Header: Authorization: Bearer <ACCESS_TOKEN>
Cookie alternative: access-token=<ACCESS_TOKEN> or access_token=<ACCESS_TOKEN>
Content-Type: application/json for JSON bodies
Books

GET /api/admin/books

Request: Headers auth only.
Success (200):
{"results": [{"id":1,"title":"Genesis","language":"en","created_at":"..."}], "count": 10}
Errors: 401, 403
POST /api/admin/books

Request body:
{"title":"New Book","language":"am","description":"...","order":1}
Success (201):
{"id":12,"title":"New Book","language":"am","description":"...","order":1}
Errors: 400 (validation), 401, 403
GET /api/admin/books/{id}

Request: auth, path param id.
Success (200):
{"id":1,"title":"Genesis","language":"en","description":"...","order":1}
Errors: 404, 401, 403
PUT /api/admin/books/{id}

Request body: partial or full update, e.g. {"title":"Updated Title"}
Success (200): updated book object
Errors: 400, 401, 403, 404
DELETE /api/admin/books/{id}

Request: auth, path param.
Success (204): empty body
Errors: 401, 403, 404
Languages

Same CRUD pattern as books using /api/admin/languages paths. Example create request:
{"code":"am","name":"Amharic","rtl":false}
Success (201): {"id":3,"code":"am","name":"Amharic","rtl":false}
Users

GET /api/admin/users

Request: auth, optional query params ?page=1&search=...
Success (200):
{"results":[{"id":1,"email":"admin@example.com","is_admin":true,"is_active":true}], "count": 5}
Errors: 401, 403
GET /api/admin/users/{id}

Success (200): {"id":2,"first_name":"A","last_name":"B","email":"u@example.com","is_admin":false,"created_at":"..."}
Errors: 404, 401, 403
PUT /api/admin/users/{id}

Request body: {"first_name":"New","last_name":"Name","is_active":true}
Success (200): updated user object
Errors: 400, 401, 403, 404
PUT /api/admin/users/{id}/admin (toggle admin)

Request body: {"is_admin": true}
Success (200): {"id":2,"is_admin":true}
Errors: 400, 401, 403, 404
GET /api/admin/users/stats

Request: auth
Success (200):
{"total_users":100,"active_users":80,"admins":3,"new_last_7_days":5}
Errors: 401, 403
GET /api/admin/users/{id}/progress

Request: auth
Success (200):
{"user_id":2,"completed_books":5,"current_book":"Matthew","last_active":"..."}
Errors: 401, 403, 404
Import / Data endpoints

GET /api/admin/import/bible

Request: auth
Success (200): {"status":"idle","last_imported":"2026-05-30T12:00:00Z","jobs":[...]}
Errors: 401, 403
POST /api/admin/import/bible

Request body: can be empty or include options, e.g. {"language":"am","mode":"full"}
Success (202):
{"job_id":"abc123","status":"started","message":"Import started"}
Errors: 400, 401, 403
GET /api/admin/import/questions

Request: auth
Success (200): {"status":"idle","last_run":"...","summary":{"added":10,"skipped":2}}
Errors: 401, 403
POST /api/admin/import/questions

Request body: {"source":"file","file_id":123} or empty if file-less trigger
Success (202): {"job_id":"qjob123","status":"started"}
Errors: 400, 401, 403
GET /api/admin/import/status

Request: auth
Success (200):
{"jobs":[{"job_id":"abc123","type":"bible","status":"running","progress":45},{"job_id":"qjob123","status":"completed"}]}
Errors: 401, 403
Common error responses (JSON)

401 Unauthorized:
{"detail":"Authentication credentials were not provided."}
403 Forbidden:
{"detail":"You do not have permission to perform this action."}
400 Bad Request (validation):
{"field_name":["error message"], "non_field_errors":["..."]}
404 Not Found:
{"detail":"Not found."}
Next step: mark draft complete and deliver final spec. Do you want these exported as a machine-readable OpenAPI snippet (YAML/JSON) or as a markdown document?

