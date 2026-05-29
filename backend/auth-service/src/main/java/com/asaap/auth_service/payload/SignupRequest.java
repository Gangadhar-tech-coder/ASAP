package com.asaap.auth_service.payload;

import lombok.Data;

@Data
public class SignupRequest {
    private String email;
    private String password;
    private String fullName;
    private String emergencyContactPhone;
    private String emergencyContactEmail;
}
