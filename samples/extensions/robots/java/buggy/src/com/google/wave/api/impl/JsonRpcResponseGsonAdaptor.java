/* Copyright (c) 2009 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.google.wave.api.impl;

import com.google.gson.JsonDeserializationContext;
import com.google.gson.JsonDeserializer;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParseException;
import com.google.gson.JsonSerializationContext;
import com.google.gson.JsonSerializer;
import com.google.gson.reflect.TypeToken;
import com.google.wave.api.BlipData;
import com.google.wave.api.JsonRpcResponse;
import com.google.wave.api.JsonRpcConstant.ParamsProperty;
import com.google.wave.api.JsonRpcConstant.ResponseProperty;

import java.lang.reflect.Type;
import java.util.HashMap;
import java.util.Map;
import java.util.Map.Entry;

/**
 * Custom serializer and deserializer that serializes and deserializes a
 * {@link JsonRpcResponse}.
 *
 * @author mprasetya@google.com (Marcel Prasetya)
 */
public class JsonRpcResponseGsonAdaptor implements JsonDeserializer<JsonRpcResponse>,
    JsonSerializer<JsonRpcResponse>{

  @Override
  public JsonRpcResponse deserialize(JsonElement json, Type type,
      JsonDeserializationContext context) throws JsonParseException {
    JsonObject jsonObject = json.getAsJsonObject();

    String id = jsonObject.get(ResponseProperty.ID.key()).getAsString();
    if (jsonObject.has(ResponseProperty.ERROR.key())) {
      JsonElement errorObject = jsonObject.get(ResponseProperty.ERROR.key());
      String errorMessage = errorObject.getAsJsonObject().get("message").getAsString();
      return JsonRpcResponse.error(id, errorMessage);
    }

    JsonObject result = null;
    // TODO(mprasetya): Do not wrap the data inside another JSON array.
    JsonElement data = jsonObject.get(ResponseProperty.DATA.key());
    if (data.isJsonArray()) {
      result = data.getAsJsonArray().get(0).getAsJsonObject();
    } else {
      result = data.getAsJsonObject();
    }

    Map<ParamsProperty, Object> properties = new HashMap<ParamsProperty, Object>();
    for (Entry<String, JsonElement> parameter : result.entrySet()) {
      ParamsProperty parameterType = ParamsProperty.fromKey(parameter.getKey());
      Object object = null;
      if (parameterType == ParamsProperty.BLIPS) {
        Type blipMapType = new TypeToken<Map<String, BlipData>>(){}.getType();
        object = context.deserialize(parameter.getValue(), blipMapType);
      } else {
        object = context.deserialize(parameter.getValue(), parameterType.clazz());
      }
      properties.put(parameterType, object);
    }

    return JsonRpcResponse.result(id, properties);
  }

  @Override
  public JsonElement serialize(JsonRpcResponse src, Type type, JsonSerializationContext context) {
    JsonObject result = new JsonObject();
    result.addProperty(ResponseProperty.ID.key(), src.getId());
    if (src.isError()) {
      JsonObject error = new JsonObject();
      error.addProperty(ParamsProperty.MESSAGE.key(), src.getErrorMessage());
      result.add(ResponseProperty.ERROR.key(), error);
    } else {
      JsonObject data = new JsonObject();
      for (Entry<ParamsProperty, Object> properties : src.getData().entrySet()) {
        data.add(properties.getKey().key(), context.serialize(properties.getValue()));
      }
      result.add(ResponseProperty.DATA.key(), data);
    }
    return result;
  }
}
