#version 330 core

in vec3 Normal;
in vec3 worldCoords;
in vec4 lightRelPos;
in float dist;

uniform sampler2D depthMap;
uniform vec3 lightPos;
uniform vec3 initialColor;
uniform float ambientStrength;

uniform float nearPlane;
uniform float farPlane;

out vec4 color;

void main()
{
    bool shadow = false;
    if (lightRelPos.w != 0) {

        vec2 texPx = lightRelPos.xy;
        float zHere = lightRelPos.z / lightRelPos.w;

        texPx = texPx * 0.5 + 0.5;
        color = vec4(texPx * 2 - 0.5, 0.0, 1.0);
        float closestDepth = texture(depthMap, texPx).r;
        float depthHere = (2.0 * nearPlane * farPlane) / ((farPlane + nearPlane - zHere * (farPlane - nearPlane)) * dist);
        shadow = closestDepth < depthHere;
    }
    float diffuseStrength = max(dot(normalize(lightPos - worldCoords), Normal), 0.0f);
    if (shadow) {
        diffuseStrength = 0.0f;
    }
    float strength = min(ambientStrength + 0.9f * diffuseStrength, 1.0f);
    color = vec4(initialColor * strength, 1.0);
}
