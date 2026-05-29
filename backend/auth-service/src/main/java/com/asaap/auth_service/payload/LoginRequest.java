package com.asaap.auth_service.payload;

import lombok.Data;

@Data
public class LoginRequest {
    private String email;
    private String password;
}
