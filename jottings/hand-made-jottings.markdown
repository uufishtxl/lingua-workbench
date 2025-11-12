# 前端 > Axios 的一些功能特性

`axios.create({config})`: 创建 axios 实例

## 配置

`withCreadentials` 用来表示是否在跨站请求中使用证书，默认值为`false`

我们这个项目的思路是：

`dj-rest-auth`使用 JWT，并通过 `my-auth-cookie` 存储和 `my-refresh-auth` 存储 Refresh
 Token，刷新断点为 `api/token/refresh`

```
# settings.py
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'my-auth-cookie', # (可选) 我们可以把 Token 存在 Cookie 里
    'JWT_AUTH_REFRESH_COOKIE': 'my-refresh-cookie', # (可选)
}
```

```python
# urls.py
urlpatters = [
	# ...
	path('api/token/refresh/', get_refresh_view().as_view(), name='token_refresh'),
	# ...
]
```

这就决定了必须在 axios 实例中配置 `withCredentials` 为 `true` 才可以使用 Cookie 中的令牌。

然后我们可以使用拦截器，在捕获到 401 错误（访问权限问题）后，自动发出刷新令牌请求。

## 我的问题和解答

### `config` 中的 `timeout`，如何针对上传请求进行超时设置
  
解决方案是可以在单次 API 请求中覆盖默认设置。比如在我们 `LoadSource.vue`文件中的 `handleUploadHttpRequest`方法里，调用 `api.post`时多传递一个配置对象即可。

```JavaScript
try {
	await apiCient.post('/v1/audios', formData, {
		headers: {
			'Content-Type': 'multipart/form-data'
		},
		timeout: 120000
	})
	handleUploadSuccess()
} catch (error) {
	ElMessage.error('Upload failed!')
	console.error(error)
}
```
   

### axios 自动转换 JSON 为 JavaScript 数据

实现转换的“幕后功臣”是 `axios`的一个核心内置功能。它的工作原理是：

1. `axios`收到后端 HTTP 响应后，会检查响应头中 `Content-Type`字段。
2. 如果发现 `Content-Type`是 `application/json`，`axios`会自动在内部使用 `JSON.parse()`来处理响应体的原始文本。
3. 这个被解析后的 JavaScript 对象或数组，最终被放到了访问的 `response.dta`属性上。

这个行为由 `axios`一个叫做 `transformReponse`的默认配置项控制。如果要处理非 JSON 格式的响应（比如 XML），也可以自定义这个配置来处理。

反之亦然，当使用 `axios.post`, `axios.put`, `axios.patch` 等方法，并且传入的 `data` 参数是一个普通的 JavaScript 对象或数组时， `axios`会自动完成以下操作：

* 自动设置 `Content-Type`：会将请求头中的 `Content-Type`自动设备为 `application/json;charset=utf-8`
* 自动 `JSON.stringify()`，将 JavaScript 对象或数组转换为 JSON 字符串
* 发送 JSON 字符串：将这个 JSON 字符串作为请求体发送出去

例外情况（不会自动 `stringify`）：

* `FormData` 对象：当传入的是一个 `FormData` 实例（比如批处理文件上传时），`axios`不会对其进行 `JSON.stringify()`。它会设置 `Content-Type`为 `multipart/form-data`，并直接发送 `FormData` 对象。
* `URLSearchParams`对象
* 原始类型：如果传入的是一个字符串、数字或布尔值等原始类型，`axios`会直接发送它们

---

## DRF > viewsets.ModelViewSet

`ModelViewSet` 是一个高度封装的类，它自动为你的模型提供了一整套标准的、符合 RESTful 风格的 CRUD (增、删、改、查) API 接口。

### `ModelViewSet` 提供的基础 CRUD 行为

当你创建一个 `ViewSet` 并继承自 `viewsets.ModelViewSet` 时，DRF 会自动为你生成以下 6 个核心的 API “动作” (actions)，并由 `Router` 自动映射到对应的 URL 和 HTTP 方法：

| 动作 (Action) | HTTP 方法 | URL 路径 | 行为描述 |
| :--- | :--- | :--- | :--- |
| `.list()` | `GET` | `/resource/` | **查询 (列表)**: 返回资源对象的列表，通常是分页的。 |
| `.retrieve()` | `GET` | `/resource/{pk}/` | **查询 (单个)**: 根据主键 `pk` 返回单个资源对象的详细信息。 |
| `.create()` | `POST` | `/resource/` | **创建**: 接收请求数据，验证后创建一个新的资源对象。 |
| `.update()` | `PUT` | `/resource/{pk}/` | **更新 (整体)**: 接收请求数据，对指定 `pk` 的对象进行**完整**更新（所有字段都需要提供）。 |
| `.partial_update()` | `PATCH` | `/resource/{pk}/` | **更新 (部分)**: 接收请求数据，对指定 `pk` 的对象进行**部分**更新（只更新提供的字段）。 |
| `.destroy()` | `DELETE` | `/resource/{pk}/` | **删除**: 根据主键 `pk` 删除一个资源对象。 |

### 为什么以及如何覆盖 (Overwrite) 这些方法

虽然 `ModelViewSet` 提供的默认行为很强大，但在真实业务场景中，我们经常需要在这些标准流程中加入**自定义的逻辑**。这就是覆盖的意义所在。

以我们的项目为例：

#### 1. 覆盖 `perform_create()` - 在创建时注入额外数据

-   **默认行为**: `.create()` 动作会调用 `serializer.save()`，直接保存从请求中获取的数据。
   - **我们的需求**: 在创建 `SourceAudio` 对象时，我们希望将这个对象与当前登录的用户关联起来，但我们**不希望**前端在请求中手动发送 `user_id`（因为这不安全）。
-   **覆盖方式**: 我们覆盖了 `.perform_create()` 方法。这个方法是 `.create()` 内部的一个“钩子”(hook)。通过在 `serializer.save()` 中传入 `user=self.request.user`，我们就在保存的那一刻，将从请求中识别出的用户对象“注入”了进去。

#### 2. 覆盖 `get_queryset()` - 实现数据权限控制

-   **默认行为**: 所有动作都基于你在 `ViewSet` 中定义的静态 `queryset` 属性，例如 `queryset = Drama.objects.all()`。这会导致所有用户都能看到**所有**的 `Drama` 对象。
-   **我们的需求**: 我们希望每个用户只能看到和操作**自己创建**的 `Drama`。
-   **覆盖方式**: 我们覆盖了 `.get_queryset()` 方法。这个方法是所有需要查询数据库的动作（如 `.list()`, `.retrieve()`）的“数据源”。通过在这个方法内部根据 `self.request.user` 动态地过滤查询集，我们从源头上就保证了用户只能访问到授权给他们的数据。

### 总结：覆盖 vs. `@action`

-   **覆盖 (Overwrite)**: 当你想要**修改或增强**一个**标准 CRUD 行为**时（例如，在创建时加点料，在查询时加个过滤条件），就覆盖对应的方法（如 `perform_create`, `get_queryset`）。
-   **`@action`**: 当你想要添加一个**全新的、非标准的 API 接口**时（例如，我们的 `create_batch`, `seasons`, `lookup`），就使用 `@action` 装饰器。


# 1.  **文件上传核心流程**: `models.FileField` 负责定义存储，`ViewSet` 中的 `parser_classes = [MultiPartParser]` 负责解析 `multipart/form-data` 请求，`ModelViewSet` 负责处理整个创建逻辑。