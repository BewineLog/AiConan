package com.capstone.aiconan.controller;

import com.capstone.aiconan.request.DetectionRequest;
import com.capstone.aiconan.response.DetectionResponse;
import com.capstone.aiconan.service.DetectionService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

@Slf4j
@RestController
@RequiredArgsConstructor
public class DetectionController {

    private final DetectionService detectionService;

    @GetMapping("/api/v1/detection")
    public void detect(@RequestBody DetectionRequest request) {

        HttpHeaders headers = new HttpHeaders();
        headers.add("Content-Type", "application/json");
        HttpEntity<DetectionRequest> entity = new HttpEntity<>(request, headers);

        //"http://falsk-api-url:8080/api"
        String url = "http://localhost:8080/api";

        RestTemplate restTemplate = new RestTemplate();

        ResponseEntity<DetectionResponse> response = restTemplate
                .exchange(url, HttpMethod.GET, entity, DetectionResponse.class);

        detectionService.recordAbnormals(response.getBody());

    }

    @GetMapping("/api/v1/test")
    public void receive() {
       log.info(">> flask API received!");

    }
}
