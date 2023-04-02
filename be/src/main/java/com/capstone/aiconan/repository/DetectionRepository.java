package com.capstone.aiconan.repository;

import com.capstone.aiconan.domain.Abnormals;
import org.springframework.data.repository.CrudRepository;

public interface DetectionRepository extends CrudRepository<Abnormals, Long> {

}
